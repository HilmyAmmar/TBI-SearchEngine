from django.shortcuts import render

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

