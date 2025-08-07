from rest_framework.routers import SimpleRouter
from .views import AuthViewSet, IndexViewSet

router = SimpleRouter()
router.register("", IndexViewSet, basename="index")
router.register("auth", AuthViewSet, basename="authentication")
