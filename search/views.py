from django.http import JsonResponse
from .elasticsearch_client import es

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
        res = es.search(index="documents", body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "abstract"]
                }
            }
        })
        hits = res["hits"]["hits"]
        results = [{"id": hit["_id"], "score": hit["_score"], "title": hit["_source"]["title"]} for hit in hits]
        return JsonResponse(results, safe=False)