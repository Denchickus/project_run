from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Run, AthleteInfo, Challenge, Position, CollectibleItem


class AthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class RunSerializer(serializers.ModelSerializer):
    athlete_data = AthleteSerializer(source='athlete', read_only=True)
    class Meta:
        model = Run
        fields = ['id', 'created_at', 'comment', 'athlete', 'athlete_data', 'status', 'run_time_seconds', 'distance']

class UserSerializer(serializers.ModelSerializer):
    # type — чтобы отличать тренеров от атлетов
    type = serializers.SerializerMethodField()
    # Добавляем вычисляемое поле (оно не хранится в БД)
    # DRF сам вызовет метод get_runs_finished()
    runs_finished = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['type', 'id', 'date_joined', 'username', 'first_name', 'last_name', 'runs_finished']

    def get_type(self, obj):
        # Тренер → True (is_staff=True), Атлет → False
        return 'coach' if obj.is_staff else 'athlete'

    def get_runs_finished(self, obj):
        """Возвращает количество завершённых забегов данного пользователя.

            obj — это текущий объект User, который сериализуется.
            Мы обращаемся к модели Run и считаем только забеги,
            у которых:
                athlete = obj (текущий пользователь)
                и status = FINISHED
        """
        return Run.objects.filter(
            athlete=obj,
            status=Run.Status.FINISHED
        ).count()

class AthleteInfoSerializer(serializers.ModelSerializer):

    # user_id мы возвращаем, но не редактируем — он берётся из URL
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = AthleteInfo
        fields = ['user_id', 'goals', 'weight']

    # Валидатор для поля weight
    def validate_weight(self, value):
        # value — это то, что прислал клиент в поле "weight"
        if value is not None and not (1 <= value <= 899):
            raise serializers.ValidationError("weight must be between 1 and 899")
        return value


class ChallengeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Challenge.
    Используется для вывода данных через API (чтение списка).
    """

    class Meta:
        model = Challenge
        fields = ['id', 'full_name', 'athlete']


class PositionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для позиции.
    Используется и для чтения, и для создания.
    """
    # Принять и вернуть формат: 2024-10-12T14:30:15.123456
    date_time = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%S.%f",
        input_formats=["%Y-%m-%dT%H:%M:%S.%f"],
    )

    class Meta:
        model = Position
        # id нужен, чтобы фронт/клиент знал, какую позицию удалять
        fields = ['id', 'run', 'latitude', 'longitude', 'created_at', 'date_time']

    def validate_latitude(self, value):
        """
        Валидация широты:
        должна быть в диапазоне [-90.0; 90.0].
        """
        if not (-90.0 <= float(value) <= 90.0):
            raise serializers.ValidationError("Latitude must be between -90.0 and 90.0")
        return value

    def validate_longitude(self, value):
        """
        Валидация долготы:
        должна быть в диапазоне [-180.0; 180.0].
        """
        if not (-180.0 <= float(value) <= 180.0):
            raise serializers.ValidationError("Longitude must be between -180.0 and 180.0")
        return value

    def validate_run(self, value):
        """
        Проверяем, что забег в статусе in_progress.
        Если забег не запущен или уже завершён – возвращаем 400 через ValidationError.
        """
        if value.status != "in_progress":
            # DRF сам превратит это в HTTP 400
            raise serializers.ValidationError("Run must be in_progress to record positions")
        return value


class CollectibleItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = CollectibleItem
        fields = ['id', 'name', 'uid', 'latitude', 'longitude', 'picture', 'value']

    def validate_latitude(self, value):
        if not (-90.0 <= value <= 90.0):
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        if not (-180.0 <= value <= 180.0):
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value

class UserDetailSerializer(serializers.ModelSerializer):
    items = CollectibleItemSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'items']



