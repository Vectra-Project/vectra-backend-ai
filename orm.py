from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os
import pytz


load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL", ""))

Base = declarative_base()

ACCESS_TOKEN_EXPIRE_HOURS = 9000 # More than a year


db_session = sessionmaker(bind=engine)
db = db_session()

TZ = pytz.timezone("Africa/Casablanca")


class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    password = Column(String(), nullable=False)
    email = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(TZ))

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


Base.metadata.create_all(engine)
