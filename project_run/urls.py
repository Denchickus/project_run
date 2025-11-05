from django.contrib import admin
from django.urls import path, include
from app_run.views import company_details
from rest_framework.routers import DefaultRouter
from app_run.views import RunViewSet, UserViewSet

router = DefaultRouter()
router.register('runs', RunViewSet, basename='runs')
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/company_details/', company_details),
    path('admin/', admin.site.urls),
]
