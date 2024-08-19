from passlib.context import CryptContext


pwd_contex = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    This function generates a hashed version of the given password using bcrypt.

    Parameters:
    password (str): The password to be hashed. It should be a string of characters.

    Returns:
    str: The hashed password. This hashed password can be safely stored in a database.
    """
    return pwd_contex.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """This function verifies password using bcrypt"""
    return pwd_contex.verify(password, hashed_password)
