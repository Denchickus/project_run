from django.db.models import Min, Max, Q, Count
from geopy.distance import geodesic

from django.conf import settings
from rest_framework.views import APIView
from django.contrib.auth.models import User

from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import status as http_status, generics, serializers
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import Run, AthleteInfo, Challenge, Position, CollectibleItem
from .serializers import RunSerializer, UserSerializer, AthleteInfoSerializer, ChallengeSerializer, PositionSerializer, \
    CollectibleItemSerializer, UserDetailSerializer
from .pagination import CustomPageNumberPagination

from openpyxl import load_workbook



@api_view(['GET'])
def company_details(request):
    data = {
        "company_name": getattr(settings, "COMPANY_NAME", "Company"),
        "slogan": getattr(settings, "COMPANY_SLOGAN", ""),
        "contacts": getattr(settings, "COMPANY_CONTACTS", ""),
    }
    return Response(data)


class RunViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с забегами атлетов.
    Поддерживает фильтрацию, сортировку, пагинацию
    и операции смены статуса (start, stop).
    """

    serializer_class = RunSerializer

    # Фильтры и сортировка
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'athlete']
    ordering_fields = ['created_at']

    # По умолчанию — без пагинации
    pagination_class = None

    def get_queryset(self):
        """
        Основной queryset + фильтр по athlete_id,
        так как это часто используемый параметр.
        """
        qs = Run.objects.select_related('athlete')
        athlete_id = self.request.query_params.get('athlete_id')

        if athlete_id:
            qs = qs.filter(athlete_id=athlete_id)

        return qs

    # -----------------------------
    #       Actions: start / stop
    # -----------------------------

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Запустить забег.
        """
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
        """
        Завершить забег.
        """
        run = self.get_object()

        if run.status != Run.Status.IN_PROGRESS:
            return Response(
                {"error": "Забег ещё не запущен или уже завершён"},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        run.status = Run.Status.FINISHED
        run.save()

        # После завершения забега — считаем время
        self.calculate_run_time(run)

        return Response({"status": run.status}, status=http_status.HTTP_200_OK)

    # -----------------------------
    # Custom list (optional paging)
    # -----------------------------

    def list(self, request, *args, **kwargs):
        """
        Если передан параметр size — включаем пагинацию.
        Иначе выводим полный queryset.
        """
        queryset = self.filter_queryset(self.get_queryset())

        if 'size' in request.query_params:
            paginator = CustomPageNumberPagination()
            paginated = paginator.paginate_queryset(queryset, request, view=self)
            serializer = self.get_serializer(paginated, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # -----------------------------
    #      Update → finish logic
    # -----------------------------

    def perform_update(self, serializer):
        """
        Если статус забега изменился именно на finished —
        пересчитываем время по Position.date_time.
        """
        instance_before = self.get_object()           # объект до изменений
        old_status = instance_before.status

        run = serializer.save()                       # объект после изменений

        if old_status != Run.Status.FINISHED and run.status == Run.Status.FINISHED:
            self.calculate_run_time(run)

    # -----------------------------
    #       Time calculation
    # -----------------------------

    def calculate_run_time(self, run):
        """
        Время забега = разница между самой ранней и самой поздней
        позицией (date_time), независимо от порядка их отправки.
        """
        agg = run.positions.aggregate(
            min_dt=Min('date_time'),
            max_dt=Max('date_time')
        )

        min_dt = agg['min_dt']
        max_dt = agg['max_dt']

        if min_dt and max_dt:
            run.run_time_seconds = int((max_dt - min_dt).total_seconds())

            # --- считаем среднюю скорость по всем позициям ---
            positions = run.positions.exclude(speed__isnull=True)

            if positions.exists():
                # здесь та самая строка avg_speed = round(sum(...), 2)
                avg_speed = round(
                    sum(p.speed for p in positions) / positions.count(),
                    2
                )
                run.speed = avg_speed

            run.save(update_fields=['run_time_seconds', 'speed'])


class UserViewSet(ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    #filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name']

    # Включаем и поиск по имени, и сортировку по дате регистрации
    filter_backends = [SearchFilter, OrderingFilter]
    ordering_fields = ['date_joined']  # Пример: ?ordering=-date_joined

    pagination_class = None

    def get_queryset(self):
        qs = User.objects.all().exclude(is_superuser=True)

        # Фильтр по типу (если нужен)
        user_type = self.request.query_params.get('type')
        if user_type == 'coach':
            qs = qs.filter(is_staff=True)
        elif user_type == 'athlete':
            qs = qs.filter(is_staff=False)

        return qs.annotate(
            runs_finished=Count(
                'run',
                filter=Q(run__status=Run.Status.FINISHED)
            )

        )

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

    def get_serializer_class(self):
        if self.action == 'retrieve':  # /api/users/ID/
            return UserDetailSerializer
        return UserSerializer  # /api/users/

class AthleteInfoView(APIView):

    # Функция, которая пытается получить объект по user_id
    def get_object(self, user_id):
        try:
            # Проверяем, существует ли пользователь
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # Если нет — возвращаем 404
            return None, Response({"error": "User not found"}, status=http_status.HTTP_404_NOT_FOUND)

        # Получаем или создаём пустую запись AthleteInfo
        athlete_info, _ = AthleteInfo.objects.get_or_create(user=user)
        return athlete_info, None

    # Получение данных (GET)
    def get(self, request, user_id):
        athlete_info, error = self.get_object(user_id)
        if error:
            return error  # Если ошибка — просто возвращаем её

        serializer = AthleteInfoSerializer(athlete_info)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # Обновление данных (PUT)
    def put(self, request, user_id):
        athlete_info, error = self.get_object(user_id)
        if error:
            return error

        # partial=True — значит можно обновить только одно поле, необязательно оба
        serializer = AthleteInfoSerializer(athlete_info, data=request.data, partial=True)

        # Проверяем, что данные корректны
        if serializer.is_valid():
            # Сохраняем изменения
            serializer.save()
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)

        # Если данные некорректны — возвращаем ошибки
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class ChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnlyModelViewSet — только для чтения.
    Возвращает список всех челленджей или фильтрует их по id атлета.
    """

    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer

    def get_queryset(self):
        """
        Если в URL есть параметр ?athlete=<id>,
        фильтруем челленджи по конкретному пользователю.
        """
        qs = super().get_queryset()
        athlete_id = self.request.query_params.get('athlete')
        if athlete_id:
            qs = qs.filter(athlete_id=athlete_id)
        return qs



class PositionViewSet(viewsets.ModelViewSet):
    """
    ViewSet для модели Position.

    Что умеет:
    - POST /api/positions/         → создать позицию
    - GET  /api/positions/         → получить все позиции
    - GET  /api/positions/?run=ID  → получить позиции только для одного забега
    - DELETE /api/positions/{id}/  → удалить конкретную позицию

    Остальное (retrieve, update) нам не так важно, но ModelViewSet их всё равно даст.
    """

    queryset = Position.objects.all()
    serializer_class = PositionSerializer

    def get_queryset(self):
        """
        Переопределяем queryset, чтобы добавить фильтрацию по run.

        Если в запросе есть параметр ?run=<run_id>,
        вернём только позиции этого забега.
        Иначе – все позиции.
        """
        qs = super().get_queryset()
        run_id = self.request.query_params.get('run')

        if run_id is not None:
            qs = qs.filter(run_id=run_id)

        return qs

    def perform_create(self, serializer):
        run = serializer.validated_data["run"]

        # 1. Проверяем статус забега
        if run.status != Run.Status.IN_PROGRESS:
            raise serializers.ValidationError("Run must be in progress to record positions")

        # 2. Создаём позицию (с date_time)
        position = serializer.save()

        # ищем предыдущую позицию
        prev_pos = Position.objects.filter(run=run).exclude(pk=position.pk).order_by('-date_time').first()
        if prev_pos is None:
            # первая точка забега
            position.speed = 0.0
            position.distance = 0.0
        else:
            # считаем расстояние (в метрах) между prev_pos и текущей позицией
            prev_point = (float(prev_pos.latitude), float(prev_pos.longitude))
            curr_point = (float(position.latitude), float(position.longitude))
            segment_meters = geodesic(prev_point, curr_point).meters

            # считаем разницу во времени в секундах
            if position.date_time and prev_pos.date_time:
                delta_seconds = (position.date_time - prev_pos.date_time).total_seconds()
            else:
                delta_seconds = 0

            # защита от деления на ноль
            if delta_seconds > 0:
                speed_m_s = segment_meters / delta_seconds
            else:
                speed_m_s = 0.0

            # накопленная дистанция: предыдущая distance + текущий отрезок в КИЛОМЕТРАХ
            # (prev_pos.distance может быть None у второй точки, поэтому подставим 0)
            prev_distance_km = prev_pos.distance or 0.0
            distance_km = prev_distance_km + (segment_meters / 1000.0)

            # округляем до сотых
            position.speed = round(speed_m_s, 2)
            position.distance = round(distance_km, 2)

        # сохраняем обновлённую позицию
        position.save(update_fields=['speed', 'distance'])
        # 3. Логика сбора предметов
        user = run.athlete

        for item in CollectibleItem.objects.all():
            distance = geodesic(
                (position.latitude, position.longitude),
                (item.latitude, item.longitude)
            ).meters

            if distance <= 100:
                item.collected_by.add(user)


class CollectibleItemView(generics.ListAPIView):
    queryset = CollectibleItem.objects.all()
    serializer_class = CollectibleItemSerializer


class UploadCollectibleFile(APIView):

    def post(self, request):
        # 1. Проверяем что файл передан
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "Файл не передан"}, status=400)

        # 2. Пытаемся загрузить Excel
        try:
            wb = load_workbook(file)
            sheet = wb.active
        except Exception:
            return Response({"error": "Неверный формат файла"}, status=400)

        invalid_rows = []

        # 3. Проходим по строкам начиная со второй (первая — заголовки)
        for row in sheet.iter_rows(min_row=2, values_only=True):

            # пропускаем полностью пустые строки
            if all(v is None for v in row):
                continue

            # порядок столбцов Excel:
            # Name, UID, Value, Latitude, Longitude, URL
            name, uid, value, lat, lon, picture = row

            data = {
                "name": name,
                "uid": uid,
                "value": value,
                "latitude": lat,
                "longitude": lon,
                "picture": picture,
            }

            serializer = CollectibleItemSerializer(data=data)

            # создаём только валидные строки
            if serializer.is_valid():
                serializer.save()
            else:
                invalid_rows.append(list(row))

        # СПИСОК невалидных строк
        return Response(invalid_rows, status=200)







