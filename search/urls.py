from django.urls import path
from .views import es_health_check, search, llm_health_check, perform_rag

urlpatterns = [
    path('es-check/', es_health_check),
    path('', search),
    path('generate/', perform_rag),
    path('llm-check/', llm_health_check),
]

