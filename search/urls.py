from django.urls import path
from .views import es_health_check

urlpatterns = [
    path('es-check/', es_health_check),
]

