from datetime import datetime
import json
from fastapi import Depends, HTTPException, Response, status
from jose import jwt, JWTError
from dotenv import load_dotenv
import os
import bcrypt
from pydantic import BaseModel
from orm import MAGIC_LINK_EXPIRY, User, TZ, db
from fastapi.security import OAuth2PasswordBearer

load_dotenv()


SECRET_KEY: str = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserInfo(BaseModel):
    first_name: str
    last_name: str
    email: str


class MagicNumberBody(BaseModel):
    magic_number: str


def generate_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(bytes(password, "utf-8"), salt)
    return hashed.decode("utf-8")


def check_password_hash(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(bytes(password, "utf-8"), bytes(hashed, "utf-8"))


def create_access_token(data: dict):
    expire = datetime.now(TZ) + MAGIC_LINK_EXPIRY
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


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

    user = db.query(User).filter_by(id=payload["sub"]).first()
    if user is None:
        raise credentials_exception

    new_token = create_access_token(data={"sub": user.email})
    response.headers["Authorization"] = f"Bearer {new_token}"

    return json.dumps(user.to_dict())
