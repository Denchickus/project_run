from django.db import models
from django.contrib.auth.models import User


class Run(models.Model):
    """Модель описывает тренировочный забег атлета"""

    class Status(models.TextChoices):
        INIT = 'init', 'Инициализирован'
        IN_PROGRESS = 'in_progress', 'В процессе'
        FINISHED = 'finished', 'Окончен'

    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()
    athlete = models.ForeignKey(User, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.INIT
    )

    def __str__(self):
        return f"Run #{self.pk} ({self.get_status_display()})"


class AthleteInfo(models.Model):
    # OneToOne — расширяем профиль пользователя дополнительными полями
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='athlete_info')

    # Цели и вес — личные данные атлета
    goals = models.CharField(max_length=255, blank=True, null=True)
    weight = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"AthleteInfo for {self.user.username}"


class Challenge(models.Model):
    """
    Модель челленджа, который атлет выполняет после 10 завершённых забегов.
    """

    # Атлет, который выполнил челлендж.
    # ForeignKey, потому что у одного атлета может быть несколько челленджей.
    athlete = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='challenges'
    )

    # Название челленджа — "Сделай 10 Забегов!"
    full_name = models.CharField(max_length=255)

    def __str__(self):
        # Строковое представление — удобно видеть в админке
        return f"{self.full_name} ({self.athlete.username})"
