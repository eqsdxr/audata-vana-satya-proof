import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    UUID,
    DateTime,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, default=uuid4(), primary_key=True)
    authenticity_count = Column(Integer, default=0)
    is_banned = Column(Boolean)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
