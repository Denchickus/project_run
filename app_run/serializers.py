from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Run

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
    # Добавляем вычисляемое поле (оно не хранится в БД)
    # DRF сам вызовет метод get_runs_finished()
    runs_finished = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'date_joined', 'username', 'first_name', 'last_name', 'runs_finished']

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

