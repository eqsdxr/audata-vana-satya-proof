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
    # Technically, the same fingerprint can be written
    # in database because if we add parameter "unique=True"
    # here, the value will be too long to be handled as unique
    # by PostgreSQL
    fingerprint = Column(Text, nullable=False)
    # Store hash for fast uniquness lookups.
    fingerprint_hash = Column(
        String(32), unique=True, nullable=False
    )  # 32 chars for md5
    # Again, we don't use "unique=True" here because if the link
    # is too long it's better to use hash instead
    file_link = Column(Text, nullable=False)
    file_link_hash = Column(
        String(32), unique=True, nullable=False
    )  # 32 chars for md5
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    # Store duration for accurate fingerprint comparisons
    duration = Column(Float, nullable=False, default=30.0)
