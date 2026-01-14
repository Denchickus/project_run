from django.db import models
from haversine import haversine, Unit
from django.contrib.auth.models import User

"""Модели базы данных для бегового трекера."""


class Run(models.Model):
    """Модель описывает тренировочный забег атлета"""

    class Status(models.TextChoices):
        INIT = "init", "Инициализирован"
        IN_PROGRESS = "in_progress", "В процессе"
        FINISHED = "finished", "Окончен"

    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True, blank=True)
    finish_time = models.DateTimeField(null=True, blank=True)
    comment = models.TextField()
    athlete = models.ForeignKey(User, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=25, choices=Status.choices, default=Status.INIT
    )

    distance = models.FloatField(default=0)  # километры
    speed = models.FloatField(null=True, blank=True)
    run_time_seconds = models.IntegerField(null=True, blank=True)

    def get_duration_seconds(self):
        """Возвращает длительность забега в секундах."""
        if self.start_time and self.finish_time:
            return int((self.finish_time - self.start_time).total_seconds())
        return None

    def save(self, *args, **kwargs):
        """
        Обрабатывает переход забега в статус FINISHED:
        рассчитывает дистанцию и начисляет выполненные челленджи.
        """

        # 1. Получаем прошлый статус
        old_status = None
        if self.pk:
            old_status = (
                Run.objects.filter(pk=self.pk).values_list("status", flat=True).first()
            )

        is_finished_transition = (
            self.status == self.Status.FINISHED and old_status != self.Status.FINISHED
        )

        # 2. Если будет переход в finished — заранее считаем distance
        if is_finished_transition:
            positions = list(
                self.positions.order_by("created_at").values_list(
                    "latitude", "longitude"
                )
            )

            total_km = 0.0
            if len(positions) >= 2:
                for i in range(len(positions) - 1):
                    p1 = (float(positions[i][0]), float(positions[i][1]))
                    p2 = (float(positions[i + 1][0]), float(positions[i + 1][1]))
                    total_km += haversine(p1, p2, unit=Unit.KILOMETERS)

            self.distance = total_km  # важно: сохраняем в километрах

        # 3. Сохраняем объект (один раз!)
        super().save(*args, **kwargs)

        # 4. Если это был переход в finished — начисляем челленджи
        if is_finished_transition:

            # --- ЧЕЛЛЕНДЖ 10 забегов ---
            finished_count = Run.objects.filter(
                athlete=self.athlete,
                status=self.Status.FINISHED,
            ).count()

            if (
                finished_count == 10
                and not Challenge.objects.filter(
                    athlete=self.athlete, full_name="Сделай 10 Забегов!"
                ).exists()
            ):
                Challenge.objects.create(
                    athlete=self.athlete, full_name="Сделай 10 Забегов!"
                )

            # --- ЧЕЛЛЕНДЖ 50 км ---
            total_distance = (
                Run.objects.filter(
                    athlete=self.athlete,
                    status=self.Status.FINISHED,
                ).aggregate(total=models.Sum("distance"))["total"]
                or 0
            )

            if (
                total_distance >= 50
                and not Challenge.objects.filter(
                    athlete=self.athlete, full_name="Пробеги 50 километров!"
                ).exists()
            ):
                Challenge.objects.create(
                    athlete=self.athlete, full_name="Пробеги 50 километров!"
                )

        # --- ЧЕЛЛЕНДЖ 2 км за 10 минут ---
        duration = self.run_time_seconds

        if (
            self.status
            == self.Status.FINISHED  # челлендж возможен только для завершённого забега
            and duration is not None  # время уже записано
            and self.distance >= 2  # километры
            and duration <= 600  # 10 минут
        ):
            if not Challenge.objects.filter(
                athlete=self.athlete, full_name="2 километра за 10 минут!"
            ).exists():
                Challenge.objects.create(
                    athlete=self.athlete, full_name="2 километра за 10 минут!"
                )

    def __str__(self):
        return f"Run #{self.pk} ({self.get_status_display()})"


class AthleteInfo(models.Model):
    """Дополнительная информация профиля атлета."""

    # OneToOne — расширяем профиль пользователя дополнительными полями
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="athlete_info"
    )

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
        User, on_delete=models.CASCADE, related_name="challenges"
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
        related_name="positions",
    )

    # Широта: от -90.0000 до +90.0000, до 4 знаков после запятой.
    # max_digits: всего цифр (до и после запятой)
    # decimal_places: сколько цифр после запятой
    latitude = models.DecimalField(
        max_digits=7,  # например: -89.9999 (7 символов вместе со знаком и целой частью)
        decimal_places=4,
    )

    # Долгота: от -180.0000 до +180.0000, тоже до 4 знаков.
    longitude = models.DecimalField(
        max_digits=8,  # например: -179.9999
        decimal_places=4,
    )

    speed = models.FloatField(null=True, blank=True)  # м/с для этого отрезка
    distance = models.FloatField(null=True, blank=True)  # накопленная дистанция в км

    # Когда точка была записана (для информации, может пригодиться позже).
    created_at = models.DateTimeField(auto_now_add=True)

    date_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        # Удобное строковое представление для админки и отладки
        return f"Run {self.run_id}: {self.latitude}, {self.longitude}"


class CollectibleItem(models.Model):
    """Коллекционный предмет, доступный для сбора во время забегов."""

    name = models.CharField(max_length=255)
    uid = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    picture = models.URLField()
    value = models.IntegerField()

    collected_by = models.ManyToManyField(
        User, related_name="items", blank=True  # user.items → предметы пользователя
    )

    def __str__(self):
        return f"{self.name} ({self.uid})"


class Subscribe(models.Model):
    """Подписка атлета на тренера с возможностью оценки."""

    athlete = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriptions",  # athlete.subscriptions → список подписок
    )
    coach = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscribers",  # coach.subscribers → кто на него подписан
    )

    rating = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("athlete", "coach")  # защитит от дублей

    def __str__(self):
        return f"{self.athlete.username} → {self.coach.username}"
