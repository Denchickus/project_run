from django.conf import settings
from django.contrib.auth.models import User

from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import Run
from .serializers import RunSerializer, UserSerializer
from .pagination import CustomPageNumberPagination


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

    # Включаем фильтры и сортировку
    filter_backends = [DjangoFilterBackend, OrderingFilter]

    # Разрешаем фильтрацию по status и athlete
    filterset_fields = ['status', 'athlete']

    # Разрешаем сортировку по created_at
    # Пример: ?ordering=created_at или ?ordering=-created_at
    ordering_fields = ['created_at']

    # По умолчанию пагинации нет → выводятся все записи
    pagination_class = None

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

    def get_list_with_optional_pagination(self, queryset):
        """
        Если пользователь передал параметр size → включаем пагинацию.
        Если size нет → возвращаем весь queryset без пагинации.
        """
        if 'size' in self.request.query_params:
            paginator = CustomPageNumberPagination()
            return paginator.paginate_queryset(queryset, self.request, view=self)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if 'size' in request.query_params:
            paginator = CustomPageNumberPagination()
            paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)
            serializer = self.get_serializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserViewSet(ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name']

    # Включаем и поиск по имени, и сортировку по дате регистрации
    filter_backends = [SearchFilter, OrderingFilter]
    ordering_fields = ['date_joined']  # Пример: ?ordering=-date_joined

    pagination_class = None

    def get_queryset(self):
        qs = User.objects.all().exclude(is_superuser=True)

        user_type = self.request.query_params.get('type')

        if user_type == 'coach':
            qs = qs.filter(is_staff=True)
        elif user_type == 'athlete':
            qs = qs.filter(is_staff=False)

        return qs

    def get_list_with_optional_pagination(self, queryset):
        if 'size' in self.request.query_params:
            paginator = CustomPageNumberPagination()
            return paginator.paginate_queryset(queryset, self.request, view=self)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Если есть параметр size → включаем пагинацию
        if 'size' in request.query_params:
            paginator = CustomPageNumberPagination()
            paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)
            serializer = self.get_serializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Если size нет → выводим все пользователи без пагинации
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

