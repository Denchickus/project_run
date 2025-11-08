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
