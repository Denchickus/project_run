# core/views.py
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import viewsets
from .models import Run
from .serializers import RunSerializer

@api_view(['GET'])
def company_details(request):
    data = {
        "company_name": getattr(settings, "COMPANY_NAME", "Company"),
        "slogan": getattr(settings, "COMPANY_SLOGAN", ""),
        "contacts": getattr(settings, "COMPANY_CONTACTS", ""),
    }
    return Response(data)

class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.all()
    serializer_class = RunSerializer

