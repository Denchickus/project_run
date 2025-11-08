from django.conf import settings
from django.contrib.auth.models import User

from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Run
from .serializers import RunSerializer, UserSerializer


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

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        run = self.get_object()

        if run.status != Run.Status.INIT:
            return Response(
                {"error": "Забег уже запущен или завершён"},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        run.status = Run.Status.IN_PROGRESS
        run.save()

        return Response({"status": run.status}, status=http_status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        run = self.get_object()

        if run.status != Run.Status.IN_PROGRESS:
            return Response(
                {"error": "Забег ещё не запущен или уже завершён"},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        run.status = Run.Status.FINISHED
        run.save()

        return Response({"status": run.status}, status=http_status.HTTP_200_OK)


class UserViewSet(ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name']

    def get_queryset(self):
        qs = User.objects.all().exclude(is_superuser=True)

        user_type = self.request.query_params.get('type')

        if user_type == 'coach':
            qs = qs.filter(is_staff=True)
        elif user_type == 'athlete':
            qs = qs.filter(is_staff=False)

        return qs
