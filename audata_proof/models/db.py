from uuid import uuid4

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    id = Column(UUID, default=uuid4(), primary_key=True)
    # Count failed authenticity checks to ban users who exceed limit
    failed_authenticity_count = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    # Use server-side timestamp to ensure consistency across time zones and avoid app-server clock drift
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    # Keep it nullable in case user use another service (whatsapp, etc.)
    # Store it as a string for simplicity
    telegram_id = Column(String(32), unique=True, nullable=True)


class Contributions(Base):
    __tablename__ = 'contributions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    # owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    # owner_telegram_id = Column(
    #    UUID(as_uuid=True), ForeignKey('users.telegram_id')
    # )
    # Store duration for accurate fingerprint comparisons
    duration = Column(Float, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    # Again, "unique=True" is not used here because if links
    # are too long so it's better to use hash instead
    file_link = Column(Text, nullable=False)
    file_link_hash = Column(
        String(32), unique=True, nullable=False
    )  # 32 chars for md5
    # Technically, the same fingerprint can be written
    # in database because if we add parameter "unique=True"
    # here, the value will be too long to be handled as unique
    # by PostgreSQL.
    # Also, when a fingerprint is stored in PostgreSQL it's converted
    # into raw bytes, so it's required to decode them before using
    fingerprint = Column(Text, nullable=False)
    # Store hash for fast uniquness lookups.
    fingerprint_hash = Column(
        String(32), unique=True, nullable=False
    )  # 32 chars for md5
