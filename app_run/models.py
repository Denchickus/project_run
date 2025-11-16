from django.db import models
from haversine import haversine, Unit
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

    distance = models.FloatField(default=0)  # километры

    def save(self, *args, **kwargs):
        """
        Переопределяем save(), чтобы:
        1) Реагировать на переход в 'finished' (Challenge)
        2) После stop — рассчитать distance по GPS точкам
        """

        # 1. Запоминаем старый статус ДО сохранения
        old_status = None
        if self.pk:
            old_status = Run.objects.filter(pk=self.pk) \
                .values_list('status', flat=True) \
                .first()

        # 2. Сохраняем объект (обновится статус)
        super().save(*args, **kwargs)

        # Реагируем ТОЛЬКО если произошёл переход в finished
        if self.status == 'finished' and old_status != 'finished':

            # --- БЛОК 1: ЧЕЛЛЕНДЖ ---
            finished_count = Run.objects.filter(
                athlete=self.athlete,
                status='finished'
            ).count()

            if finished_count == 10 and not Challenge.objects.filter(
                    athlete=self.athlete,
                    full_name="Сделай 10 Забегов!"
            ).exists():
                Challenge.objects.create(
                    athlete=self.athlete,
                    full_name="Сделай 10 Забегов!"
                )

            # --- БЛОК 2: РАСЧЁТ DISTANCE ---
            positions = list(
                self.positions.order_by('created_at')
                .values_list('latitude', 'longitude')
            )

            total_km = 0.0

            # Если точек достаточно — считаем
            if len(positions) >= 2:
                for i in range(len(positions) - 1):
                    point1 = (float(positions[i][0]), float(positions[i][1]))
                    point2 = (float(positions[i + 1][0]), float(positions[i + 1][1]))
                    segment = haversine(point1, point2, unit=Unit.KILOMETERS)
                    total_km += segment

            # Записываем вычисленную дистанцию
            self.distance = total_km

            # Сохраняем ТОЛЬКО distance, чтобы не вызвать повторный save()
            super().save(update_fields=['distance'])

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


class Position(models.Model):
    """
    Позиция атлета во время забега.
    Хранит ссылку на забег и координаты (широту и долготу).
    """

    # К какому забегу относятся координаты.
    # related_name='positions' → потом сможем делать: run.positions.all()
    run = models.ForeignKey(
        Run,
        on_delete=models.CASCADE,
        related_name='positions',
    )

    # Широта: от -90.0000 до +90.0000, до 4 знаков после запятой.
    # max_digits: всего цифр (до и после запятой)
    # decimal_places: сколько цифр после запятой
    latitude = models.DecimalField(
        max_digits=7,     # например: -89.9999 (7 символов вместе со знаком и целой частью)
        decimal_places=4,
    )

    # Долгота: от -180.0000 до +180.0000, тоже до 4 знаков.
    longitude = models.DecimalField(
        max_digits=8,     # например: -179.9999
        decimal_places=4,
    )

    # Когда точка была записана (для информации, может пригодиться позже).
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Удобное строковое представление для админки и отладки
        return f"Run {self.run_id}: {self.latitude}, {self.longitude}"
