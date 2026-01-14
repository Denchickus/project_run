import pytest
from django.contrib.auth.models import User

from runs.models import Run


@pytest.mark.django_db
def test_start_changes_status_to_in_progress(client):
    athlete = User.objects.create_user(username="a1", password="pass", is_staff=False)
    run = Run.objects.create(athlete=athlete, comment="c", status=Run.Status.INIT)

    response = client.post(f"/api/runs/{run.id}/start/")
    assert response.status_code == 200

    run.refresh_from_db()
    assert run.status == Run.Status.IN_PROGRESS


@pytest.mark.django_db
def test_start_twice_returns_400(client):
    athlete = User.objects.create_user(username="a2", password="pass", is_staff=False)
    run = Run.objects.create(athlete=athlete, comment="c", status=Run.Status.INIT)

    r1 = client.post(f"/api/runs/{run.id}/start/")
    assert r1.status_code == 200

    r2 = client.post(f"/api/runs/{run.id}/start/")
    assert r2.status_code == 400


@pytest.mark.django_db
def test_stop_without_start_returns_400(client):
    athlete = User.objects.create_user(username="a3", password="pass", is_staff=False)
    run = Run.objects.create(athlete=athlete, comment="c", status=Run.Status.INIT)

    response = client.post(f"/api/runs/{run.id}/stop/")
    assert response.status_code == 400


@pytest.mark.django_db
def test_stop_after_start_sets_finished(client):
    athlete = User.objects.create_user(username="a4", password="pass", is_staff=False)
    run = Run.objects.create(athlete=athlete, comment="c", status=Run.Status.INIT)

    client.post(f"/api/runs/{run.id}/start/")
    response = client.post(f"/api/runs/{run.id}/stop/")

    assert response.status_code == 200

    run.refresh_from_db()
    assert run.status == Run.Status.FINISHED


@pytest.mark.django_db
def test_start_nonexistent_run_returns_404(client):
    response = client.post("/api/runs/999999/start/")
    assert response.status_code == 404
