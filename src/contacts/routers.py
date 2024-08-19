from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter

from src.auth.schemas import RoleEnum
from src.auth.models import User
from src.auth.utils import RoleChecker, get_current_user
from config.db import get_db
from src.contacts.repo import ContactsRepository
from src.contacts.schemas import ContactsCreate, ContactsResponse

router = APIRouter()


@router.get("/ping")
def hello() -> dict:
    """
    This function returns a simple "ping-pong" message.

    Parameters:
    None

    Returns:
    dict: A dictionary containing a "message" key with the value "pong".
    """
    return {"message": "pong"}


@router.post(
    "/",
    response_model=ContactsResponse,
    dependencies=[
        Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN])),
        Depends(RateLimiter(times=10, seconds=60)),
    ],
    status_code=status.HTTP_201_CREATED,
)
def create_contacts(
    contact: ContactsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new contact in the database.

    Parameters:
    contact (ContactsCreate): The contact data to be created.
    current_user (User, optional): The current user making the request. Defaults to Depends(get_current_user).
    db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
    ContactsResponse: The newly created contact.

    Raises:
    HTTPException: If the current user does not have the required role.
    """
    repo = ContactsRepository(db)
    return repo.create_contacts(contact, current_user.id)


@router.get(
    "/",
    response_model=list[ContactsResponse],
    dependencies=[
        Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN])),
        Depends(RateLimiter(times=10, seconds=60)),
    ],
)
def get_contacts(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ContactsResponse]:
    """
    Retrieves a list of contacts from the database based on the current user's role and pagination parameters.

    Parameters:
    limit (int, optional): The maximum number of contacts to retrieve. Defaults to 10.
    offset (int, optional): The number of contacts to skip before starting to retrieve. Defaults to 0.
    current_user (User, optional): The current user making the request. Defaults to Depends(get_current_user).
    db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
    list[ContactsResponse]: A list of retrieved contacts.
    """
    repo = ContactsRepository(db)
    return repo.get_contacts(current_user.id, limit, offset)


@router.get(
    "/all/",
    response_model=list[ContactsResponse],
    dependencies=[
        Depends(RoleChecker([RoleEnum.ADMIN])),
        Depends(RateLimiter(times=10, seconds=60)),
    ],
    tags=["admin"],
)
def get_contacts_all(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[ContactsResponse]:
    """
    Retrieves all contacts from the database for admin users.

    Parameters:
    limit (int, optional): The maximum number of contacts to retrieve. Defaults to 10.
    offset (int, optional): The number of contacts to skip before starting to retrieve. Defaults to 0.
    db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
    list[ContactsResponse]: A list of retrieved contacts.
    """
    repo = ContactsRepository(db)
    return repo.get_contacts_all(limit, offset)


@router.get(
    "/search/",
    response_model=list[ContactsResponse],
    dependencies=[
        Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN])),
        Depends(RateLimiter(times=10, seconds=60)),
    ],
)
def search_contacts(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ContactsResponse]:
    """
    This function searches for contacts based on a given query.

    Parameters:
    query (str): The search query string.
    current_user (User, optional): The current user making the request. Defaults to Depends(get_current_user).
    db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
    list[ContactsResponse]: A list of contacts that match the search query.
    """
    repo = ContactsRepository(db)
    return repo.search_contacts(current_user.id, query)


@router.delete("/{contact_id}", dependencies=[Depends(RoleChecker([RoleEnum.ADMIN]))])
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """
    Deletes a contact from the database based on the provided contact ID.

    Parameters:
    contact_id (int): The unique identifier of the contact to be deleted.
    db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
    dict: A confirmation message indicating the successful deletion of the contact.

    Raises:
    HTTPException: If the contact with the given ID is not found in the database.
    """
    repo = ContactsRepository(db)
    contact = repo.get_contact_by_id(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    repo.delete_contact(contact_id)
    return {"message": f"Contact {contact_id} deleted"}


@router.get("/upcoming_birthdays/")
def get_upcoming_birthdays(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 7,
) -> list[ContactsResponse]:
    """
    Retrieves a list of upcoming birthdays for the current user's contacts.

    Parameters:
    current_user (User, optional): The current user making the request. Defaults to Depends(get_current_user).
    db (Session, optional): The database session. Defaults to Depends(get_db).
    days (int, optional): The number of days in the future to consider for upcoming birthdays. Defaults to 7.

    Returns:
    list[ContactsResponse]: A list of contacts with upcoming birthdays. Each contact is represented by a ContactsResponse object.
    """
    repo = ContactsRepository(db)
    return repo.get_upcoming_birthdays(current_user.id, days)


@router.put("/{identifier}", response_model=ContactsResponse)
def update_contact(
    identifier: str,
    contact_update: ContactsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates an existing contact in the database based on the provided identifier.

    Parameters:
    identifier (str): The unique identifier of the contact to be updated.
    contact_update (ContactsCreate): The updated contact data.
    current_user (User, optional): The current user making the request. Defaults to Depends(get_current_user).
    db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
    ContactsResponse: The updated contact.

    Raises:
    HTTPException: If the contact with the given identifier is not found in the database.
    """
    repo = ContactsRepository(db)
    updated_contact = repo.update_contact(identifier, current_user.id, contact_update)
    if updated_contact:
        return updated_contact
    else:
        raise HTTPException(status_code=404, detail="Contact not found")
