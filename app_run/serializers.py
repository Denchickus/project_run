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
        fields = ['id', 'created_at', 'comment', 'athlete', 'athlete_data']

class UserSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'date_joined', 'username', 'first_name', 'last_name', 'type']

    def get_type(self, obj):
        return 'coach' if obj.is_staff else 'athlete'

