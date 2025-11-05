# core/views.py
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import viewsets
from .models import Run
from .serializers import RunSerializer, UserSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet
from django.contrib.auth.models import User

@api_view(['GET'])
def company_details(request):
    data = {
        "company_name": getattr(settings, "COMPANY_NAME", "Company"),
        "slogan": getattr(settings, "COMPANY_SLOGAN", ""),
        "contacts": getattr(settings, "COMPANY_CONTACTS", ""),
    }
    return Response(data)

class RunViewSet(viewsets.ModelViewSet):
    serializer_class = RunSerializer

    def get_queryset(self):
        qs = Run.objects.select_related('athlete')
        athlete_id = self.request.query_params.get('athlete_id')
        if athlete_id:
            qs = qs.filter(athlete_id=athlete_id)
        return qs


class UserViewSet(ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        qs = User.objects.all()
        qs = qs.exclude(is_superuser=True)  # скрываем админов

        user_type = self.request.query_params.get('type')

        if user_type == 'coach':
            qs = qs.filter(is_staff=True)
        elif user_type == 'athlete':
            qs = qs.filter(is_staff=False)

        return qs



