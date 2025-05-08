from django.urls import path
from .views import es_health_check, search

urlpatterns = [
    path('es-check/', es_health_check),
    path('search/', search),
]

