from django.urls import path
from .views import (
    AthleteInfoView,
    CollectibleItemView,
    UploadCollectibleFile,
)

urlpatterns = [
    # Информация об атлете
    path('athlete_info/<int:user_id>/', AthleteInfoView.as_view()),

    # Список Collectible Items
    path('collectible_item/', CollectibleItemView.as_view()),

    # Загрузка Excel-файла
    path('upload_file/', UploadCollectibleFile.as_view()),
]
