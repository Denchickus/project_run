import pytest


@pytest.mark.django_db
def test_company_details(client):
    response = client.get("/api/company_details/")

    assert response.status_code == 200

    data = response.json()

    assert "company_name" in data
    assert "slogan" in data
    assert "contacts" in data
