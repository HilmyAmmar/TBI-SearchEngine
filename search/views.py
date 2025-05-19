from django.shortcuts import render

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