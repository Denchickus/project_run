from django.urls import path
from .views import AthleteInfoView

urlpatterns = [
    path('athlete_info/<int:user_id>/', AthleteInfoView.as_view()),
]
