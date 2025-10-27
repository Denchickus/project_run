from django.urls import path
from .views import company_details

urlpatterns = [
    path('company_details/', company_details, name='company_details'),
]
