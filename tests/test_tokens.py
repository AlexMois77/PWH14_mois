from datetime import timedelta
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.auth.schemas import TokenData
from src.auth.utils import create_access_token, decode_access_token
from main import app
from src.contacts.models import Contact
import logging

logging.getLogger("faker.factory").setLevel(logging.ERROR)

client = TestClient(app)


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
