from datetime import datetime, timedelta
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv
import os
import pytz

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

Base = declarative_base()

Auth_Session = sessionmaker(bind=engine)
db = Auth_Session()

TZ = pytz.timezone("Africa/Casablanca")


class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    password = Column(String(), nullable=False)
    email = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(TZ))
    sessions = relationship("Auth_Session", back_populates="user")

    def __repr__(self):
        return f"User(user_id={self.user_id}, first_name={self.first_name}, last_name={self.last_name}, password={self.password}, email={self.email}, created_at={self.created_at})"

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "created_at": str(self.created_at),
        }

    @staticmethod
    def get_by_email(email):
        return db.query(User).filter_by(email=email).first()


class Auth_Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    user = relationship("User", back_populates="sessions")
    start_timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(TZ))
    last_activity_timestamp = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(TZ),
        onupdate=lambda: datetime.now(TZ),
    )

    def __repr__(self):
        return f"Auth_Session(session_id={self.id}, user_id={self.user_id}, start_timestamp={self.start_timestamp}, last_activity_timestamp={self.last_activity_timestamp})"


Base.metadata.create_all(engine)


def create_session(user_id: Integer):
    session_id = str(uuid.uuid4())
    session = Auth_Session(id=session_id, user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session_id


def get_session(session_id: str):
    current_time = datetime.now(TZ)
    session = (
        db.query(Auth_Session)
        .filter(
            Auth_Session.id == session_id,
            current_time < current_time + timedelta(hours=4),
        )
        .first()
    )
    if session:
        user = session.user
        return user.to_dict()
    else:
        return None


def delete_session(session_id: str):
    db.query(Auth_Session).filter(Auth_Session.id == session_id).delete()
    db.commit()
