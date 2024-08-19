import pytest
from fastapi import status
from fastapi.testclient import TestClient
from src.contacts.models import Contact


def test_ping(client: TestClient):
    response = client.get("/ping")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "pong"}


def test_create_contact(client: TestClient, auth_headers, db_session):
    response = client.post(
        "/contacts/",
        headers=auth_headers,
        json={
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com",
            "phone_number": "1234567890",
            "birthday": "1990-01-01",
            "additional_info": "Additional info",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Smith"
    assert data["email"] == "john.smith@example.com"


def test_get_contacts(
    client: TestClient, auth_headers, test_user, test_user_contact: Contact
):
    response = client.get("/contacts/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    contacts = response.json()
    assert len(contacts) == 1
    assert contacts[0]["email"] == test_user_contact.email


def test_get_contacts_all(
    client: TestClient, auth_headers, test_user, test_user_contact: Contact
):
    response = client.get("/contacts/all/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    contacts = response.json()
    assert len(contacts) == 1
    assert contacts[0]["email"] == test_user_contact.email


def test_search_contacts(
    client: TestClient, auth_headers, test_user, test_user_contact: Contact
):
    response = client.get(
        f"/contacts/search/?query={test_user_contact.email}", headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    contacts = response.json()
    assert len(contacts) == 1
    assert contacts[0]["email"] == test_user_contact.email


def test_delete_contact(client: TestClient, auth_headers, test_user_contact: Contact):
    response = client.delete(f"/contacts/{test_user_contact.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": f"Contact {test_user_contact.id} deleted"}

    # Verify deletion
    response = client.get(f"/contacts/{test_user_contact.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_upcoming_birthdays(
    client: TestClient, auth_headers, test_user, test_user_contact: Contact
):
    response = client.get("/contacts/upcoming_birthdays/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    contacts = response.json()
    assert len(contacts) == 1
    assert contacts[0]["email"] == test_user_contact.email


def test_update_contact(client: TestClient, auth_headers, test_user_contact: Contact):
    response = client.put(
        f"/contacts/{test_user_contact.id}",
        headers=auth_headers,
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe.updated@example.com",
            "phone_number": "0987654321",
            "birthday": "1992-02-02",
            "additional_info": "Updated info",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    updated_contact = response.json()
    assert updated_contact["email"] == "jane.doe.updated@example.com"

    # Verify update
    response = client.get(f"/contacts/{test_user_contact.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    contact = response.json()
    assert contact["email"] == "jane.doe.updated@example.com"
