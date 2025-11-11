from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Run, AthleteInfo

class AthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class RunSerializer(serializers.ModelSerializer):
    athlete_data = AthleteSerializer(source='athlete', read_only=True)
    class Meta:
        model = Run
        fields = ['id', 'created_at', 'comment', 'athlete', 'athlete_data', 'status']

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

