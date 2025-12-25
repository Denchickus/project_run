from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AthleteInfoView,
    CollectibleItemView,
    UploadCollectibleFile,
    UserViewSet,
    subscribe_to_coach,
    challenges_summary,
    rate_coach,
    analytics_for_coach,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("athlete_info/<int:user_id>/", AthleteInfoView.as_view()),
    path("collectible_item/", CollectibleItemView.as_view()),
    path("upload_file/", UploadCollectibleFile.as_view()),
    path("subscribe_to_coach/<int:id>/", subscribe_to_coach),
    path("challenges_summary/", challenges_summary),
    path("rate_coach/<int:coach_id>/", rate_coach),
    path("analytics_for_coach/<int:coach_id>/", analytics_for_coach),
    path("", include(router.urls)),
]
