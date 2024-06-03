import bcrypt
from pydantic import BaseModel


class UserLogin(BaseModel):
    email: str
    password: str


class UserInfo(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


def generate_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(bytes(password, "utf-8"), salt)
    return hashed


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(bytes(password, "utf-8"), hashed)
