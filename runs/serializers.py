from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    Run,
    AthleteInfo,
    Challenge,
    Position,
    CollectibleItem,
    Subscribe,
)

"""Сериализаторы DRF для API бегового трекера."""

# ============================================================
#                    ВСПОМОГАТЕЛЬНЫЕ СЕРИАЛИЗАТОРЫ
# ============================================================


class AthleteSerializer(serializers.ModelSerializer):
    """Краткая информация об атлете."""

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class RunSerializer(serializers.ModelSerializer):
    """Забег + вложенная информация об атлете."""

    athlete_data = AthleteSerializer(source="athlete", read_only=True)

    class Meta:
        model = Run
        fields = [
            "id",
            "created_at",
            "comment",
            "athlete",
            "athlete_data",
            "status",
            "run_time_seconds",
            "distance",
            "speed",
        ]


# ============================================================
#                    LIST: /api/users/
# ============================================================


class UserBaseSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для списка пользователей.
    /api/users/
    """

    type = serializers.SerializerMethodField()
    runs_finished = serializers.IntegerField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    rating = serializers.FloatField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "type",
            "date_joined",
            "runs_finished",
            "rating",
        ]

    def get_type(self, user: User) -> str:
        return "coach" if user.is_staff else "athlete"


# ============================================================
#                    DETAIL: /api/users/<id>/
# ============================================================


class AthleteDetailSerializer(UserBaseSerializer):
    """
    Детальный сериализатор для АТЛЕТА.
    + coach
    + items
    """

    coach = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + ["coach", "items"]

    def get_coach(self, user: User):
        sub = Subscribe.objects.filter(athlete=user).first()
        return sub.coach.id if sub else None

    def get_items(self, user: User):
        return CollectibleItemSerializer(user.items.all(), many=True).data


class CoachDetailSerializer(UserBaseSerializer):
    """
    Детальный сериализатор профиля тренера
    + athletes
    + items
    """

    athletes = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + ["athletes", "items"]

    def get_athletes(self, coach: User):
        return list(
            Subscribe.objects.filter(coach=coach).values_list("athlete_id", flat=True)
        )

    def get_items(self, coach: User):
        return CollectibleItemSerializer(coach.items.all(), many=True).data


class SubscribeSerializer(serializers.Serializer):
    """Сериализатор запроса на подписку атлета на тренера."""

    athlete = serializers.IntegerField()


class AthleteInfoSerializer(serializers.ModelSerializer):
    """Информация об атлете: цели, вес."""

    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = AthleteInfo
        fields = ["user_id", "goals", "weight"]

    def validate_weight(self, value):
        if value is not None and not (1 <= value <= 899):
            raise serializers.ValidationError("weight must be between 1 and 899")
        return value


class ChallengeSerializer(serializers.ModelSerializer):
    """Сериализатор выполненных челленджей."""

    class Meta:
        model = Challenge
        fields = ["id", "full_name", "athlete"]


class PositionSerializer(serializers.ModelSerializer):
    """Позиция атлета во время забега."""

    date_time = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%S.%f",
        input_formats=["%Y-%m-%dT%H:%M:%S.%f"],
    )

    class Meta:
        model = Position
        fields = [
            "id",
            "run",
            "latitude",
            "longitude",
            "created_at",
            "date_time",
            "speed",
            "distance",
        ]
        read_only_fields = ["speed", "distance"]

    def validate_latitude(self, value):
        if not (-90.0 <= float(value) <= 90.0):
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        if not (-180.0 <= float(value) <= 180.0):
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value

    def validate_run(self, value):
        if value.status != "in_progress":
            raise serializers.ValidationError(
                "Run must be in_progress to record positions"
            )
        return value


class CollectibleItemSerializer(serializers.ModelSerializer):
    """Сериализатор коллекционных предметов."""

    class Meta:
        model = CollectibleItem
        fields = ["id", "name", "uid", "latitude", "longitude", "picture", "value"]

    def validate_latitude(self, value):
        if not (-90 <= value <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        if not (-180 <= value <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value


class RateCoachSerializer(serializers.Serializer):
    """Сериализатор оценки тренера атлетом."""

    athlete = serializers.IntegerField()
    rating = serializers.IntegerField()

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
