import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_create_run_returns_init_status(client):
    # 1) создаём атлета (is_staff=False)
    athlete = User.objects.create_user(
        username="athlete1",
        password="pass12345",
        first_name="Ivan",
        last_name="Petrov",
        is_staff=False,
    )

    # 2) отправляем POST на создание забега
    payload = {
        "athlete": athlete.id,
        "comment": "Первый забег",
    }

    response = client.post("/api/runs/", data=payload)

    # 3) проверяем ответ
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["athlete"] == athlete.id
    assert data["comment"] == "Первый забег"
    assert data["status"] == "init"
