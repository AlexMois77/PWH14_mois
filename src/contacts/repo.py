from datetime import datetime, timedelta
from typing import List
from sqlalchemy import extract, or_, select, update

from src.contacts.models import Contact
from src.contacts.schemas import ContactsCreate


class ContactsRepository:
    def __init__(self, session):
        """
        Initialize a new instance of ContactsRepository.

        This class provides methods for interacting with the Contacts database table.
        It uses SQLAlchemy ORM to perform database operations.

        Parameters:
        session (Session): A SQLAlchemy session object for database interaction.

        Returns:
        None
        """
        self.session = session

    def get_contacts(self, owner_id, limit: int = 10, offset: int = 0) -> List[Contact]:
        """
        Retrieves a list of contacts for the specified owner from the database with pagination support.

        This function constructs a SQLAlchemy query to select contacts from the Contacts table where the owner_id
        matches the provided owner_id. The query includes pagination support, allowing retrieval of a specified number
        of contacts at a time, starting from a given offset.

        Parameters:
        owner_id (int): The ID of the owner for whom to retrieve contacts.
        limit (int): The maximum number of contacts to retrieve per page. Default is 10.
        offset (int): The number of contacts to skip before starting to retrieve. Default is 0.

        Returns:
        List[Contact]: A list of Contact objects retrieved from the database.
        """
        query = (
            select(Contact)
            .where(Contact.owner_id == owner_id)
            .limit(limit)
            .offset(offset)
        )
        results = self.session.execute(query)
        return results.scalars().all()

    def get_contacts_all(self, limit: int = 10, offset: int = 0) -> List[Contact]:
        """
        Retrieve all contacts from the database with pagination support.

        This function retrieves a list of contacts from the database based on the provided limit and offset.
        It uses SQLAlchemy ORM to execute the query and returns a list of Contact objects.

        Parameters:
        limit (int): The maximum number of contacts to retrieve per page. Default is 10.
        offset (int): The number of contacts to skip before starting to retrieve. Default is 0.

        Returns:
        List[Contact]: A list of Contact objects retrieved from the database.
        """
        query = select(Contact).limit(limit).offset(offset)
        results = self.session.execute(query)
        return results.scalars().all()

    def create_contacts(self, contact: ContactsCreate, owner_id: int) -> Contact:
        """
        Creates a new contact in the database for the specified owner.

        This function takes a ContactsCreate object and an owner_id as input. It creates a new Contact
        object using the provided data and associates it with the specified owner. The new contact is then
        added to the database session, committed, refreshed, and returned.

        Parameters:
        contact (ContactsCreate): A ContactsCreate object containing the data for the new contact.
        owner_id (int): The ID of the owner for whom the new contact is being created.

        Returns:
        Contact: The newly created Contact object.
        """
        new_contact = Contact(**contact.model_dump(), owner_id=owner_id)
        self.session.add(new_contact)
        self.session.commit()
        self.session.refresh(new_contact)
        return new_contact

    def search_contacts(self, owner_id, query):
        """
        Search for contacts based on the given owner_id and query.

        This function performs a case-insensitive search on the first_name, last_name, and email fields
        of the Contacts database table for the specified owner_id. The search is performed using the
        provided query string.

        Parameters:
        owner_id (int): The ID of the owner for whom to search contacts.
        query (str): The search query string.

        Returns:
        List[Contact]: A list of Contact objects that match the search criteria.
        """
        q = (
            select(Contact)
            .where(Contact.owner_id == owner_id)
            .filter(
                (Contact.first_name.ilike(f"%{query}%"))
                | (Contact.last_name.ilike(f"%{query}%"))
                | (Contact.email.ilike(f"%{query}%"))
            )
        )
        results = self.session.execute(q)
        return results.scalars().all()

    def get_contact_by_id_and_owner(self, owner_id: int, contact_id: int) -> Contact:
        """
        Retrieve a contact from the database based on the provided owner_id and contact_id.

        This function constructs a SQLAlchemy query to select a single contact from the Contacts table
        where the owner_id matches the provided owner_id and the contact_id matches the provided contact_id.
        The query is executed using the provided SQLAlchemy session and the result is returned.

        Parameters:
        owner_id (int): The ID of the owner for whom to retrieve the contact.
        contact_id (int): The ID of the contact to retrieve.

        Returns:
        Contact: The contact object with the matching owner_id and contact_id, or None if no such contact exists.
        """
        q = select(Contact).where(
            Contact.owner_id == owner_id, Contact.id == contact_id
        )
        result = self.session.execute(q)
        return result.scalar_one_or_none()

    def get_contact_by_id(self, contact_id: int) -> Contact:
        """
        Retrieve a contact from the database based on the provided contact_id.

        This function constructs a SQLAlchemy query to select a single contact from the Contacts table
        where the contact_id matches the provided contact_id. The query is executed using the provided
        SQLAlchemy session and the result is returned.

        Parameters:
        contact_id (int): The ID of the contact to retrieve.

        Returns:
        Contact: The contact object with the matching contact_id, or None if no such contact exists.
        """
        query = select(Contact).where(Contact.id == contact_id)
        result = self.session.execute(query)
        return result.scalar_one_or_none()

    def delete_contact(self, contact_id: int):
        """
        Deletes a contact from the database based on the provided contact_id.

        This function retrieves a contact from the database using the provided contact_id.
        If the contact exists, it is deleted from the database and the session is committed.

        Parameters:
        contact_id (int): The ID of the contact to delete.

        Returns:
        None
        """
        contact = self.session.get(Contact, contact_id)
        if contact:
            self.session.delete(contact)
            self.session.commit()

    def get_upcoming_birthdays(self, owner_id: int, days: int = 7) -> List[Contact]:
        """
        Retrieves a list of contacts who have birthdays within the specified number of days from today.

        This function calculates the upcoming birthdays based on the current date and the provided number of days.
        It then constructs a SQLAlchemy query to select contacts from the database where the owner_id matches the provided
        owner_id and the contact's birthday falls within the specified range.

        Parameters:
        owner_id (int): The ID of the owner for whom to retrieve upcoming birthdays.
        days (int): The number of days from today to consider for upcoming birthdays. Default is 7.

        Returns:
        List[Contact]: A list of Contact objects who have birthdays within the specified number of days from today.
        """
        today = datetime.today()
        upcoming_date = today + timedelta(days=days)
        today_day_of_year = today.timetuple().tm_yday
        upcoming_day_of_year = upcoming_date.timetuple().tm_yday

        if today_day_of_year <= upcoming_day_of_year:
            query = select(Contact).filter(
                Contact.owner_id == owner_id,
                extract("doy", Contact.birthday).between(
                    today_day_of_year, upcoming_day_of_year
                ),
            )
        else:
            query = select(Contact).filter(
                Contact.owner_id == owner_id,
                or_(
                    extract("doy", Contact.birthday) >= today_day_of_year,
                    extract("doy", Contact.birthday) <= upcoming_day_of_year,
                ),
            )

        results = self.session.execute(query)
        return results.scalars().all()

    def find_contact(self, owner_id: int, identifier: str) -> Contact:
        """
        Finds a contact in the database based on the provided owner_id and identifier.

        The function attempts to convert the identifier to an integer and uses it to search for a contact by ID.
        If the conversion fails, it treats the identifier as a string and performs a search based on email,
        first name, or full name (first name + last name).

        Parameters:
        owner_id (int): The ID of the owner for whom to find the contact.
        identifier (str): The identifier to search for. This can be a contact ID (converted to int), email,
        first name, or full name.

        Returns:
        Contact: The contact object with the matching owner_id and identifier, or None if no such contact exists.
        """
        try:
            contact_id = int(identifier)
        except ValueError:
            contact_id = None

        query = select(Contact).where(
            Contact.owner_id == owner_id,
            or_(
                Contact.id == contact_id,
                Contact.email == identifier,
                Contact.first_name == identifier,
                (Contact.first_name + " " + Contact.last_name) == identifier,
            ),
        )
        result = self.session.execute(query)
        return result.scalar_one_or_none()

    def update_contact(
        self, identifier: str, owner_id: int, contact_update: ContactsCreate
    ) -> Contact:
        """
        Updates a contact in the database based on the provided identifier and owner_id.

        This function first finds the contact using the provided identifier and owner_id.
        If the contact is found, it checks if the email in the contact_update object is unique among all contacts.
        If the email is unique, it updates the contact's information using the provided contact_update object.
        The updated contact is then committed to the database and returned.

        Parameters:
        identifier (str): The identifier to search for. This can be a contact ID (converted to int), email, first name, or full name.
        owner_id (int): The ID of the owner for whom to find and update the contact.
        contact_update (ContactsCreate): A ContactsCreate object containing the updated contact information.

        Returns:
        Contact: The updated contact object, or None if no contact is found with the provided identifier and owner_id.
        """
        contact = self.find_contact(owner_id, identifier)
        if not contact:
            return None

        if contact_update.email:
            existing_contact = self.session.execute(
                select(Contact).where(Contact.email == contact_update.email)
            ).scalar_one_or_none()
            if existing_contact and existing_contact.id != contact.id:
                raise ValueError("Email already in use")

        stmt = (
            update(Contact)
            .where(Contact.id == contact.id)
            .values(contact_update.model_dump(exclude_unset=True))
            .returning(Contact)
        )
        result = self.session.execute(stmt)
        self.session.commit()
        updated_contact = result.scalar()
        return updated_contact
