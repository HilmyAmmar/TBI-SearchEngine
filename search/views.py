import re
from django.http import JsonResponse
from .elasticsearch_client import es
from .mistral_client import client

def es_health_check(request):
    try:
        info = es.info()
        return JsonResponse({
            "name": info['name'],
            "cluster_name": info['cluster_name'],
            "version": info['version']['number'],
            "status": "connected"
        })
    except Exception as e:
        return JsonResponse({"status": "error", "detail": str(e)}, status=500)

def llm_health_check(request):
    try:
        completion = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            messages=[
                {"role": "user", "content": "What is the capital of Indonesia?"}
            ],
        )

        return JsonResponse({
            "status": "connected",
            "response_snippet": completion.choices[0].message.content
        })
    except Exception as e:
        return JsonResponse({"status": "error", "detail": str(e)}, status=500)

def expand_query(query: str) -> list[str]:
    """
    Expand query with relevant medical terms for better search results.
    """
    prompt = f"""
    You are a medical search assistant. Generate 3-5 relevant medical terms, synonyms, or related concepts for the query below.
    Focus on medical terminology, alternative names, and closely related conditions.
    Return ONLY the terms separated by commas, without numbering or extra text.

    Query: "{query}"
    """

    try:
        expansion = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )

        expanded_raw = expansion.choices[0].message.content.strip()
        # Clean up the response
        cleaned = re.sub(r'\d+\.\s*', '', expanded_raw)
        cleaned = cleaned.replace('\n', ',')
        expanded_terms = [term.strip() for term in cleaned.split(',') if term.strip()]
        
        # Limit to 5 terms to avoid noise
        return expanded_terms[:5]
    except Exception as e:
        print(f"Query expansion failed: {e}")
        return []

def search_with_rag(request):
    """
    Unified search function that:
    1. Receives query and k parameter
    2. Expands the query
    3. Searches for top k documents
    4. Performs RAG with the retrieved documents
    5. Returns both LLM answer and top k documents
    """
    if request.method != 'GET':
        return JsonResponse({"status": "error", "detail": "Use GET method"}, status=405)

    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({"status": "error", "detail": "Query is required"}, status=400)

    # Get configurable k parameter (default to 5)
    try:
        k = int(request.GET.get('k', 5))
        k = max(1, min(k, 20))  # Limit k between 1 and 20
    except ValueError:
        k = 5

    try:
        # Step 1: Expand the query
        expanded_terms = expand_query(query)
        
        # Step 2: Build enhanced search query
        # Combine original query with expanded terms
        search_query = query
        if expanded_terms:
            search_query = f"{query} {' '.join(expanded_terms)}"

        # Step 3: Search for top k documents using expanded query
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,  # Original query as main requirement
                                "fields": ["title^3", "abstract^2", "main_text"],
                                "type": "best_fields"
                            }
                        }
                    ],
                    "should": [
                        # Boost with expanded terms
                        {
                            "multi_match": {
                                "query": " ".join(expanded_terms),
                                "fields": ["title^2", "abstract", "main_text"],
                                "type": "cross_fields"
                            }
                        }
                    ],
                    "minimum_should_match": 0
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "abstract": {},
                    "main_text": {"fragment_size": 150}
                }
            }
        }

        res = es.search(index="medicine", size=k, body=search_body)
        hits = res["hits"]["hits"]

        # Step 4: Prepare documents for both return and RAG context
        documents = []
        context_parts = []

        for i, hit in enumerate(hits, 1):
            source = hit["_source"]
            
            # Document info for return
            doc_info = {
                "rank": i,
                "id": hit["_id"],
                "score": hit["_score"],
                "title": source["title"],
                "abstract": source.get("abstract", "")[:300] + "..." if len(source.get("abstract", "")) > 300 else source.get("abstract", ""),
                "url": source.get("url", ""),
                "highlights": hit.get("highlight", {})
            }
            documents.append(doc_info)

            # Context for RAG (include more text)
            doc_context = f"""Document {i}:
Title: {source["title"]}
Abstract: {source.get("abstract", "")}
Content: {source["main_text"][:800]}{"..." if len(source["main_text"]) > 800 else ""}
"""
            context_parts.append(doc_context)

        # Step 5: Perform RAG with retrieved documents
        if documents:
            full_context = "\n\n".join(context_parts)
            
            rag_prompt = f"""You are a medical expert assistant. Based on the provided medical documents, answer the user's question comprehensively and accurately.

Use the information from the documents below to provide a detailed, evidence-based answer. If the documents don't contain sufficient information to fully answer the question, clearly state what information is missing.

Medical Documents:
{full_context}

Question: {query}

Please provide a comprehensive answer based on the medical documents above:"""

            try:
                rag_response = client.chat.completions.create(
                    model="mistralai/Mistral-7B-Instruct-v0.3",
                    messages=[
                        {"role": "user", "content": rag_prompt}
                    ],
                    max_tokens=600,
                    temperature=0.2  # Lower temperature for more factual responses
                )
                
                llm_answer = rag_response.choices[0].message.content
            except Exception as e:
                llm_answer = f"Error generating answer: {str(e)}"
        else:
            llm_answer = "No relevant documents found to answer your question."

        # Step 6: Return comprehensive response
        return JsonResponse({
            "query": {
                "original": query,
                "expanded_terms": expanded_terms,
                "final_search_query": search_query
            },
            "search_results": {
                "total_found": res["hits"]["total"]["value"],
                "returned_count": len(documents),
                "k_requested": k,
                "documents": documents
            },
            "rag_answer": {
                "answer": llm_answer,
                "confidence": "high" if len(documents) >= 3 else "medium" if len(documents) >= 1 else "low"
            }
        })

    except Exception as e:
        return JsonResponse({"status": "error", "detail": str(e)}, status=500)

# Keep the old functions for backward compatibility, but mark them as deprecated
def search(request):
    """DEPRECATED: Use search_with_rag instead"""
    return search_with_rag(request)

def perform_rag(request):
    """DEPRECATED: Use search_with_rag instead"""
    return search_with_rag(request)