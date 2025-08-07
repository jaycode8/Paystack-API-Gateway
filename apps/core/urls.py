from .router import router
from django.urls import path, include

urlpatterns = [
    path("", include(router.urls))
]