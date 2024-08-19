import unittest
from unittest.mock import MagicMock
from faker import Faker
from datetime import datetime, timedelta

from sqlalchemy import extract, or_, select
from src.contacts.models import Contact
from src.contacts.schemas import ContactsCreate
from src.contacts.repo import ContactsRepository
from sqlalchemy.orm.session import Session


class TestContactsRepository(unittest.TestCase):
    def setUp(self):
        self.faker = Faker()
        self.session = MagicMock(spec=Session)
        self.repo = ContactsRepository(self.session)

        self.owner_id = self.faker.random_int(min=1, max=1000)
        self.contact_id = self.faker.random_int(min=1, max=1000)
        self.contact_email = self.faker.email()
        self.contact_first_name = self.faker.first_name()
        self.contact_last_name = self.faker.last_name()
        self.contact_birthday = self.faker.date_of_birth(minimum_age=18, maximum_age=90)

        self.contact_mock = MagicMock(spec=Contact)
        self.contact_mock.id = self.contact_id
        self.contact_mock.owner_id = self.owner_id
        self.contact_mock.email = self.contact_email
        self.contact_mock.first_name = self.contact_first_name
        self.contact_mock.last_name = self.contact_last_name
        self.contact_mock.birthday = self.contact_birthday

    def test_get_contacts(self):
        self.session.execute.return_value.scalars.return_value.all.return_value = [
            self.contact_mock
        ]
        contacts = self.repo.get_contacts(self.owner_id)
        self.assertEqual(contacts, [self.contact_mock])
        self.session.execute.assert_called_once()

    def test_get_contacts_all(self):
        self.session.execute.return_value.scalars.return_value.all.return_value = [
            self.contact_mock
        ]
        contacts = self.repo.get_contacts_all()
        self.assertEqual(contacts, [self.contact_mock])
        self.session.execute.assert_called_once()

    def test_create_contacts(self):
        contact_create = MagicMock(spec=ContactsCreate)
        contact_create.first_name = self.faker.first_name()
        contact_create.last_name = self.faker.last_name()
        contact_create.email = self.faker.email()
        contact_create.birthday = self.faker.date_of_birth(
            minimum_age=18, maximum_age=90
        )

        self.session.execute.return_value.scalar_one_or_none.return_value = None
        new_contact = self.repo.create_contacts(contact_create, self.owner_id)
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(new_contact)

    def test_search_contacts(self):
        self.session.execute.return_value.scalars.return_value.all.return_value = [
            self.contact_mock
        ]
        query = self.faker.word()
        contacts = self.repo.search_contacts(self.owner_id, query)
        self.assertEqual(contacts, [self.contact_mock])
        self.session.execute.assert_called_once()

    def test_get_contact_by_id_and_owner(self):
        self.session.execute.return_value.scalar_one_or_none.return_value = (
            self.contact_mock
        )
        contact = self.repo.get_contact_by_id_and_owner(self.owner_id, self.contact_id)
        self.assertEqual(contact, self.contact_mock)
        self.session.execute.assert_called_once()

    def test_get_contact_by_id(self):
        self.session.execute.return_value.scalar_one_or_none.return_value = (
            self.contact_mock
        )
        contact = self.repo.get_contact_by_id(self.contact_id)
        self.assertEqual(contact, self.contact_mock)
        self.session.execute.assert_called_once()

    def test_delete_contact(self):
        self.session.get.return_value = self.contact_mock
        self.repo.delete_contact(self.contact_id)
        self.session.delete.assert_called_once_with(self.contact_mock)
        self.session.commit.assert_called_once()

    def test_get_upcoming_birthdays(self):
        today = datetime.today()
        upcoming_date = today + timedelta(days=7)
        today_day_of_year = today.timetuple().tm_yday
        upcoming_day_of_year = upcoming_date.timetuple().tm_yday

        self.session.execute.return_value.scalars.return_value.all.return_value = [
            self.contact_mock
        ]

        contacts = self.repo.get_upcoming_birthdays(self.owner_id, days=7)
        self.assertEqual(contacts, [self.contact_mock])

        if today_day_of_year <= upcoming_day_of_year:
            query = select(Contact).filter(
                Contact.owner_id == self.owner_id,
                extract("doy", Contact.birthday).between(
                    today_day_of_year, upcoming_day_of_year
                ),
            )
        else:
            query = select(Contact).filter(
                Contact.owner_id == self.owner_id,
                or_(
                    extract("doy", Contact.birthday) >= today_day_of_year,
                    extract("doy", Contact.birthday) <= upcoming_day_of_year,
                ),
            )

        self.session.execute.assert_called_once()

    def test_find_contact(self):
        contact_id = self.faker.random_int(min=1, max=1000)
        contact_email = self.faker.email()
        query = self.faker.word()

        self.session.execute.return_value.scalar_one_or_none.return_value = (
            self.contact_mock
        )

        contact = self.repo.find_contact(self.owner_id, contact_id)
        self.assertEqual(contact, self.contact_mock)

        contact = self.repo.find_contact(self.owner_id, contact_email)
        self.assertEqual(contact, self.contact_mock)

        contact = self.repo.find_contact(self.owner_id, query)
        self.assertEqual(contact, self.contact_mock)

        self.session.execute.assert_called()

    def test_update_contact(self):
        contact_update = MagicMock(spec=ContactsCreate)
        contact_update.email = self.faker.email()
        contact_update.first_name = self.faker.first_name()
        contact_update.last_name = self.faker.last_name()

        self.session.execute.return_value.scalar_one_or_none.return_value = (
            self.contact_mock
        )
        self.session.execute.return_value.scalar.return_value = self.contact_mock

        updated_contact = self.repo.update_contact(
            self.contact_id, self.owner_id, contact_update
        )
        self.assertEqual(updated_contact, self.contact_mock)
        self.session.execute.assert_called()
        self.session.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
