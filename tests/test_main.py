import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


@pytest.mark.asyncio
async def test_read_main(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
