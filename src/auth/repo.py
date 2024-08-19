from functools import lru_cache
from fastapi import HTTPException, status
from sqlalchemy import select

from src.auth.models import Role, User
from src.auth.schemas import RoleEnum, UserCreate
from src.auth.pass_utils import get_password_hash


class UserRepository:
    def __init__(self, session):
        self.session = session

    def create_user(self, user_create: UserCreate) -> User:
        """
        Creates a new user in the database.

        Parameters:
        user_create (UserCreate): An instance of UserCreate containing the necessary information for creating a new user.

        Returns:
        User: The newly created user instance.
        """
        hashed_password = get_password_hash(user_create.password)
        user_role = RoleRepository(self.session).get_role_by_name(user_create.role)
        new_user = User(
            username=user_create.username,
            hashed_password=hashed_password,
            email=user_create.email,
            role_id=user_role.id,  # Setting the role ID
            is_active=False,
        )
        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)
        return new_user

    def get_user(self, username: str) -> User:
        """
        Retrieves a user from the database based on their username.

        Parameters:
        username (str): The username of the user to retrieve.

        Returns:
        User: The user with the specified username. If no user is found, returns None.
        """
        query = select(User).where(User.username == username)
        result = self.session.execute(query)
        return result.scalar_one_or_none()

    def get_user_by_email(self, email: str) -> User:
        """
        Retrieves a user from the database based on their email address.

        Parameters:
        email (str): The email address of the user to retrieve.

        Returns:
        User: The user with the specified email address. If no user is found, returns None.
        This function uses SQLAlchemy's select statement to query the database for a user with the given email address.
        If a user is found, it is returned. Otherwise, None is returned.
        """
        query = select(User).where(User.email == email)
        result = self.session.execute(query)
        return result.scalar_one_or_none()

    def activate_user(self, user: User):
        """
        Activates a user in the database.

        Parameters:
        user (User): The user instance to be activated. The user's 'is_active' attribute will be set to True.

        Returns:
        None: This function does not return any value. It updates the 'is_active' attribute of the given user in the database.
        """
        user.is_active = True
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

    def update_avatar(self, email: str, url: str) -> User:
        """
        Updates the avatar URL of a user in the database based on their email address.

        Parameters:
        email (str): The email address of the user whose avatar needs to be updated.
        url (str): The new avatar URL to be set for the user.

        Returns:
        User: The updated user instance with the new avatar URL. If the user is not found,
        an HTTPException with a 404 status code and a "User not found" detail is raised.

        This function first queries the database for a user with the given email address.
        If a user is found, the avatar URL is updated, the changes are committed to the database,
        and the updated user instance is refreshed from the database before being returned.
        If no user is found, an HTTPException is raised.
        """
        query = select(User).where(User.email == email)
        result = self.session.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        user.avatar = url
        self.session.commit()
        self.session.refresh(user)
        return user


class RoleRepository:
    def __init__(self, session):
        self.session = session

    @lru_cache
    def get_role_by_name(self, name: RoleEnum):
        """
        Retrieves a role from the database based on its name.
        Parameters:
        name (RoleEnum): The name of the role to retrieve. The name is expected to be a member of the RoleEnum class.
        Returns:
        Role: The role with the specified name. If no role is found, returns None.
        This function uses SQLAlchemy's select statement to query the database for a role with the given name.
        The result is cached using the lru_cache decorator to improve performance.
        If a role is found, it is returned. Otherwise, None is returned.
        """
        query = select(Role).where(Role.name == name.value)
        result = self.session.execute(query)
        return result.scalar_one_or_none()
