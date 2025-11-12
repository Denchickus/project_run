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

    def save(self, *args, **kwargs):
        """
        Переопределяем save, чтобы отреагировать на переход в finished
        вне зависимости от того, откуда он пришёл (update, кастомный action, admin, shell).
        """
        # Определяем старый статус (если объект уже существует)
        old_status = None
        if self.pk:
            old_status = Run.objects.filter(pk=self.pk).values_list('status', flat=True).first()

        super().save(*args, **kwargs)  # сначала сохраняем текущее изменение

        # После сохранения — если случился ПЕРЕХОД в 'finished'
        if self.status == 'finished' and old_status != 'finished':
            # Избегаем циклического импорта
            from .models import Challenge  # если Challenge в том же файле, импорт не нужен

            finished_count = Run.objects.filter(athlete=self.athlete, status='finished').count()

            # Создаём челлендж только на РОВНО 10-й финиш и только если его ещё нет
            if finished_count == 10 and not Challenge.objects.filter(
                    athlete=self.athlete,
                    full_name="Сделай 10 Забегов!"
            ).exists():
                Challenge.objects.create(
                    athlete=self.athlete,
                    full_name="Сделай 10 Забегов!"
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
