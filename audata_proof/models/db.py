from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Integer,
    UUID,
    DateTime,
    String,
    Text,
    func,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"

    id = Column(UUID, default=uuid4(), primary_key=True)
    # Count failed authenticity checks to ban users who exceed limit
    failed_authenticity_count = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    # Use server-side timestamp to ensure consistency across time zones and avoid app-server clock drift
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


class Contributions(Base):
    __tablename__ = "contributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    fingerprint = Column(Text, nullable=False)
    # Store hash too for fast uniquness lookups
    fingerprint_hash = Column(String(32), unique=True, nullable=False) # 32 chars for md5
    file_link = Column(Text, unique=True, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    # Store duration for accurate fingerprint comparisons
    duration = Column(Float, nullable=False, default=30.0)
