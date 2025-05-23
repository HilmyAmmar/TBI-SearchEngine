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

def search(request):
    if request.method == 'GET':
        query = request.GET.get('q', 'default')
        res = es.search(index="medicine", size=10, body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "abstract"]
                }
            }
        })
        hits = res["hits"]["hits"]
        results = [{
            "id": hit["_id"], 
            "url": hit["_source"]["url"], 
            "score": hit["_score"], 
            "title": hit["_source"]["title"],
            "text": hit["_source"]["main_text"]
        } for hit in hits]
        return JsonResponse(results, safe=False)

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
    
def expand_query(request):
    try:
        if request.method != 'GET':
            return JsonResponse({"status": "error", "detail": "Gunakan metode GET"}, status=405)

        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({"status": "error", "detail": "Query kosong"}, status=400)

        prompt = f"""
        You are an intelligent search assistant. Expand the user's query with relevant terms ONLY, without changing the original intent. 
        Do NOT include unrelated meanings, ambiguous words, or overly general terms. 
        Return exactly 10 highly related keywords or phrases that can help improve search accuracy. 
        Return the terms separated ONLY by commas, without numbering, newlines, or extra characters.

        Query: "{query}"
        """

        expansion = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        expanded_raw = expansion.choices[0].message.content.strip()

        cleaned = re.sub(r'\d+\.\s*', '', expanded_raw)  
        cleaned = cleaned.replace('\n', ',')

        expanded_terms = [term.strip() for term in cleaned.split(',') if term.strip()]

        return JsonResponse({
            "original_query": query,
            "expanded_query": expanded_terms
        })

    except Exception as e:
        return JsonResponse({"status": "error", "detail": str(e)}, status=500)
    
def perform_rag(request):
    try:
        if request.method == 'GET':
            query = request.GET.get('q', 'default')
            res = es.search(index="medicine", size=4, body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "abstract"]
                    }
                }
            })
            hits = res["hits"]["hits"]
            results = [hit["_source"]["main_text"] for hit in hits]

            texts = "\n\n".join(results)

            prompt = f"""
            Answer the question based on the context below:

            Context:
            {texts}

            Question: {query}    
            """
            rag = client.chat.completions.create(
                model="mistralai/Mistral-7B-Instruct-v0.3",
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            return JsonResponse(rag, safe=False)
    except Exception as e:
        return JsonResponse({"status": "error", "detail": str(e)}, status=500)


