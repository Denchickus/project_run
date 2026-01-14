import pytest
from django.contrib.auth.models import User
from runs.models import Run


@pytest.mark.django_db
def test_cannot_create_position_if_run_not_in_progress(client):
    athlete = User.objects.create_user(
        username="athlete_pos1",
        password="pass",
        is_staff=False,
    )

    run = Run.objects.create(
        athlete=athlete,
        comment="run",
        status=Run.Status.INIT,   # ❗ забег не запущен
    )

    payload = {
        "run": run.id,
        "latitude": 55.7558,
        "longitude": 37.6173,
        "date_time": "2024-10-12T14:30:15.123456",
    }

    response = client.post("/api/positions/", data=payload)

    assert response.status_code == 400


@pytest.mark.django_db
def test_create_position_if_run_in_progress(client):
    athlete = User.objects.create_user(
        username="athlete_pos2",
        password="pass",
        is_staff=False,
    )

    run = Run.objects.create(
        athlete=athlete,
        comment="run",
        status=Run.Status.IN_PROGRESS,   # ✅ забег идёт
    )

    payload = {
        "run": run.id,
        "latitude": 55.7558,
        "longitude": 37.6173,
        "date_time": "2024-10-12T14:30:15.123456",
    }

    response = client.post("/api/positions/", data=payload)

    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["run"] == run.id

