from .views import ProductsViewSet
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register("", ProductsViewSet, basename="product")