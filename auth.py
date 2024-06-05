from datetime import datetime, timedelta
import json
from fastapi import Depends, HTTPException, Response, status
from jose import jwt, JWTError
from dotenv import load_dotenv
import os
import bcrypt
from pydantic import BaseModel
from orm import ACCESS_TOKEN_EXPIRE_HOURS, User, TZ
from fastapi.security import OAuth2PasswordBearer

load_dotenv()


SECRET_KEY: str = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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
    return hashed.decode("utf-8")


def check_password_hash(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(bytes(password, "utf-8"), bytes(hashed, "utf-8"))


def create_access_token(data: dict):
    expire = datetime.now(TZ) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def authenticate_user(email: str, password: str) -> User | None:
    user = User.get_by_email(email)
    if not user:
        return None
    if not check_password_hash(password, str(user.password)):
        return None
    return user


def get_current_user(response: Response, token: str = Depends(oauth2_scheme)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception

    if datetime.fromtimestamp(payload["exp"], TZ) < datetime.now(TZ):
        raise credentials_exception

    user = User.get_by_email(payload["sub"])
    if user is None:
        raise credentials_exception

    new_token = create_access_token(data={"sub": user.email})
    response.headers["Authorization"] = f"Bearer {new_token}"

    return json.dumps(user.to_dict())
