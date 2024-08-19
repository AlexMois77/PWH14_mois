import logging
import unittest
from unittest.mock import MagicMock, patch
from faker import Faker
from src.auth.models import User, Role
from src.auth.repo import UserRepository, RoleRepository
from src.auth.schemas import RoleEnum
from fastapi import HTTPException

logging.basicConfig(level=logging.WARNING)


class TestUserRepository(unittest.TestCase):

    def setUp(self):
        self.faker = Faker()
        self.session = MagicMock()
        self.repo = UserRepository(self.session)

        self.username = self.faker.user_name()
        self.email = self.faker.email()
        self.password = self.faker.password()
        self.role = RoleEnum.USER

        self.user_create_mock = MagicMock()
        self.user_create_mock.username = self.username
        self.user_create_mock.email = self.email
        self.user_create_mock.password = self.password
        self.user_create_mock.role = self.role

        self.role_mock = MagicMock()
        self.role_mock.id = 1

        with patch.object(
            RoleRepository, "get_role_by_name", return_value=self.role_mock
        ):
            self.new_user = self.repo.create_user(self.user_create_mock)

    def test_create_user(self):
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(self.new_user)

        self.assertEqual(self.new_user.username, self.username)
        self.assertEqual(self.new_user.email, self.email)
        self.assertEqual(self.new_user.role_id, 1)

    def test_get_user(self):
        self.session.execute.return_value.scalar_one_or_none.return_value = (
            self.new_user
        )
        user = self.repo.get_user(self.username)
        self.assertEqual(user.username, self.username)

    def test_get_user_by_email(self):
        self.session.execute.return_value.scalar_one_or_none.return_value = (
            self.new_user
        )
        user = self.repo.get_user_by_email(self.email)
        self.assertEqual(user.email, self.email)

    def test_activate_user(self):
        self.assertFalse(self.new_user.is_active)

        self.repo.activate_user(self.new_user)

        self.assertTrue(self.new_user.is_active)
        self.session.add.assert_called_with(self.new_user)
        self.session.commit.assert_called()
        self.session.refresh.assert_called_with(self.new_user)

    def test_update_avatar(self):
        avatar_url = self.faker.image_url()

        self.session.execute.return_value.scalar_one_or_none.return_value = (
            self.new_user
        )

        updated_user = self.repo.update_avatar(self.email, avatar_url)

        self.assertEqual(updated_user.avatar, avatar_url)
        self.assertEqual(
            self.session.commit.call_count, 2
        )  # Проверка на 1 вызов commit
        self.assertEqual(self.session.refresh.call_count, 2)  # Проверка на 2

    def test_update_avatar_user_not_found(self):
        self.session.execute.return_value.scalar_one_or_none.return_value = None

        avatar_url = self.faker.image_url()

        with self.assertRaises(HTTPException) as context:
            self.repo.update_avatar(self.email, avatar_url)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "User not found")


class TestRoleRepository(unittest.TestCase):

    def setUp(self):
        self.session = MagicMock()
        self.repo = RoleRepository(self.session)
        self.role_name = RoleEnum.USER
        self.role_mock = MagicMock()
        self.role_mock.name = self.role_name.value
        self.session.execute.return_value.scalar_one_or_none.return_value = (
            self.role_mock
        )

    def test_get_role_by_name(self):
        role = self.repo.get_role_by_name(self.role_name)
        self.assertEqual(role.name, self.role_name.value)
        self.session.execute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
