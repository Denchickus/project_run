from django.contrib import admin
from django.urls import path, include
from runs.views import company_details
from rest_framework.routers import DefaultRouter
from runs.views import RunViewSet, UserViewSet, ChallengeViewSet, PositionViewSet

router = DefaultRouter()
router.register("runs", RunViewSet, basename="runs")
router.register("users", UserViewSet, basename="users")
router.register("challenges", ChallengeViewSet, basename="challenges")
router.register("positions", PositionViewSet, basename="positions")


urlpatterns = [
    path("api/", include(router.urls)),
    path("api/", include("runs.urls")),
    path("api/company_details/", company_details),
    path("admin/", admin.site.urls),
]
