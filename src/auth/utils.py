import os
import cloudinary.uploader

from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from src.auth.repo import UserRepository
from src.auth.schemas import UserResponse
from src.auth.models import User
from config.db import get_db
from src.auth.schemas import RoleEnum, TokenData
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
VERIFICATION_TOKEN_HOUSE = 24


def create_verification_token(email: str) -> str:
    """
    This function generates a JWT verification token for a given email address.

    Parameters:
    email (str): The email address for which the verification token is being generated.

    Returns:
    str: The generated JWT verification token.
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_HOUSE)
    to_encode = {"exp": expire, "sub": email}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_verification_token(token: str) -> str | None:
    """
    This function decodes a JWT verification token and extracts the email address.

    Parameters:
    token (str): The JWT verification token to be decoded.

    Returns:
    str | None: The email address extracted from the token if it is valid and not expired.
    Returns None if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    This function generates a JWT access token with an optional expiration time.

    Parameters:
    data (dict): A dictionary containing the data to be encoded in the JWT.
    expires_delta (timedelta, optional): A timedelta object representing the token's expiration time.
    If not provided, the token will expire after ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
    str: The generated JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(f"Access token created2: {encoded_jwt}")
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    This function generates a JWT refresh token with an optional expiration time.

    Parameters:
    data (dict): A dictionary containing the data to be encoded in the JWT. This data should include the user's identifier (e.g., email).
    expires_delta (timedelta, optional): A timedelta object representing the token's expiration time.
    If not provided, the token will expire after REFRESH_TOKEN_EXPIRE_DAYS.

    Returns:
    str: The generated JWT refresh token. This token can be used to obtain a new access token without requiring user credentials.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(f"Refresh token created2: {encoded_jwt}")
    return encoded_jwt


def decode_access_token(token: str) -> TokenData | None:
    """
    Decodes a JWT access token and extracts the username from the payload.

    Parameters:
    token (str): The JWT access token to be decoded.

    Returns:
    TokenData | None: An instance of TokenData containing the username if the token is valid and not expired.
    Returns None if the token is invalid or expired.

    Raises:
    JWTError: If the token cannot be decoded due to invalid signature or expired time.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except JWTError as e:
        print(f"JWTError: {e}")
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> UserResponse:
    """
    Retrieves the current user based on the provided JWT access token.

    Parameters:
    token (str): The JWT access token used to authenticate the user.
    This parameter is optional and defaults to the value provided by the `oauth2_scheme` dependency.
    db (Session): The database session object used to interact with the database.
    This parameter is optional and defaults to the value provided by the `get_db` dependency.

    Returns:
    UserResponse: An instance of UserResponse containing the details of the current user.
    If the token is invalid or the user does not exist, an HTTPException is raised.

    Raises:
    HTTPException: If the token is invalid or the user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exception
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_email(token_data.username)
    if user is None:
        raise credentials_exception
    return user


def upload_image_to_cloudinary(file):
    """
    Uploads an image file to Cloudinary and returns the secure URL of the uploaded image.

    Parameters:
    file (str or file-like object): The image file to be uploaded. This can be a file path, a file-like object, or a URL.

    Returns:
    str: The secure URL of the uploaded image on Cloudinary.

    Raises:
    CloudinaryException: If an error occurs during the upload process.
    """
    response = cloudinary.uploader.upload(file)
    return response["secure_url"]


class RoleChecker:
    def __init__(self, allowed_roles: list[RoleEnum]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
    ) -> User:
        """
        This method is a dependency that checks if the user associated with the provided JWT token has the required role.
        If the user's role is not in the list of allowed roles, an HTTPException is raised with a 403 Forbidden status code.

        Parameters:
        token (str): The JWT access token used to authenticate the user.
                    This parameter is optional and defaults to the value provided by the `oauth2_scheme` dependency.
        db (Session): The database session object used to interact with the database.
                    This parameter is optional and defaults to the value provided by the `get_db` dependency.

        Returns:
        User: The user object associated with the provided JWT token.
            If the user's role is not in the list of allowed roles, an HTTPException is raised.

        Raises:
        HTTPException: If the user's role is not in the list of allowed roles.
        """
        user = get_current_user(token, db)
        if user and user.role.name not in [role.value for role in self.allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this resource",
            )
        return user
