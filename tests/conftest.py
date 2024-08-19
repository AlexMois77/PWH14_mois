from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.auth.utils import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
)
from src.auth.pass_utils import get_password_hash
from src.auth.schemas import RoleEnum
from config.db import Base, get_db
from main import app
from src.auth.models import User, Role
from src.contacts.models import Contact
import os

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(setup_db):
    session = TestingSessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture(scope="function")
def override_get_db(db_session):
    def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def user_password():
    return "test_password"


@pytest.fixture(scope="function")
def user_role(db_session):
    role = db_session.query(Role).filter_by(name=RoleEnum.USER.value).first()
    if not role:
        role = Role(name=RoleEnum.USER.value)
        db_session.add(role)
        db_session.commit()
    return role


@pytest.fixture(scope="function")
def test_user(db_session, user_password, user_role):
    # Хэшируем пароль пользователя
    hashed_password = get_password_hash(user_password)

    # Создаем нового пользователя
    new_user = User(
        username="test_user",
        email="test_user@example.com",
        is_active=True,
        hashed_password=hashed_password,
        role_id=user_role.id,
    )

    # Добавляем пользователя в базу данных
    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)

    # Создаем токены для нового пользователя
    access_token = create_access_token(data={"sub": new_user.username})
    refresh_token = create_refresh_token(data={"sub": new_user.username})

    print(f"Access token: {access_token}, {new_user.username}")
    # Возвращаем пользователя и токены
    return {
        "user": new_user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@pytest.fixture(scope="function", autouse=True)
def mock_rate_limiter():
    with patch("fastapi_limiter.depends.RateLimiter", new_callable=AsyncMock):
        yield


@pytest.fixture(scope="function")
def auth_headers(test_user):
    access_token = create_access_token(data={"sub": test_user.username})
    refresh_token = create_refresh_token(data={"sub": test_user.username})

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Refresh-Token": refresh_token,
        "Content-Type": "application/json",
    }
    print(f"Access token1: {access_token}, {test_user.username}")
    print(f"Refresh token1: {refresh_token}, {test_user.email}")

    return headers


@pytest.fixture(scope="function")
def test_user_contact(db_session, test_user):

    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="123456789",
        birthday="1990-01-01",
        user_id=test_user.id,
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)
    return contact


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
