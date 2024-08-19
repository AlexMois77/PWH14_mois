from datetime import timedelta
from unittest.mock import AsyncMock, patch
import jwt
import pytest
from fastapi.testclient import TestClient
from src.auth.schemas import TokenData
from src.auth.utils import create_access_token, decode_access_token
from main import app
from src.contacts.models import Contact
import logging

logging.getLogger("faker.factory").setLevel(logging.ERROR)

client = TestClient(app)

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"


@pytest.fixture
def valid_token():
    payload = {"sub": "test_user"}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


@pytest.fixture
def expired_token():
    payload = {"sub": "test_user"}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM, expires_at=-1)
    return token


@pytest.fixture
def invalid_token():
    return "invalid_token"


def test_decode_access_token_success():
    access_token = create_access_token(data={"sub": "test_user"})
    decoded_token = decode_access_token(access_token)
    assert decoded_token is not None
    assert decoded_token.username == "test_user"


def test_decode_access_token_expired():
    expired_token = create_access_token(
        data={"sub": "test_user"}, expires_delta=-timedelta(minutes=1)
    )
    decoded_token = decode_access_token(expired_token)
    assert decoded_token is None


def test_decode_access_token_invalid(invalid_token):
    token_data = decode_access_token(invalid_token)
    assert token_data is None


def test_create_contact(test_user, override_get_db):
    # Формируем заголовки с токенами
    auth_headers = {
        "Authorization": f"Bearer {test_user['access_token']}",
        "X-Refresh-Token": test_user["refresh_token"],
        "Content-Type": "application/json",
    }

    # Отправляем запрос
    response = client.post(
        "/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone_number": "123456789",
            "birthday": "1990-01-01",
        },
        headers=auth_headers,
    )

    # Печатаем и проверяем статус
    print(f"headers: {response.content}")
    print(f"Status code: {response.status_code}")
    print(f"Response JSON: {response.json()}")

    assert response.status_code == 201
    data = response.json()
    assert data["owner_id"] == test_user["user"].id
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["email"] == "john.doe@example.com"
    assert data["phone_number"] == "123456789"
    assert data["birthday"] == "1990-01-01"
    assert "additional_info" in data
    assert data["additional_info"] == "Some info"


# def test_get_contact(override_get_db, test_user_contact: Contact, auth_headers):
#     response = client.get(f"/contacts/{test_user_contact.id}", headers=auth_headers)

#     assert response.status_code == 200
#     data = response.json()
#     assert data["id"] == test_user_contact.id
#     assert data["first_name"] == test_user_contact.first_name
#     assert data["last_name"] == test_user_contact.last_name
#     assert data["email"] == test_user_contact.email
#     assert data["phone_number"] == test_user_contact.phone_number
#     assert data["birthday"] == test_user_contact.birthday
#     assert "additional_info" in data
#     assert data["additional_info"] == test_user_contact.additional_info
