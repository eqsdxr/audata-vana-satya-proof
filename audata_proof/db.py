from contextlib import contextmanager
from typing import Generator

from loguru import logger as console_logger
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from audata_proof.config import settings
from audata_proof.models.db import Base


class Database:
    def __init__(self):
        self._engine = None
        self._SessionLocal = None

    def init(self) -> None:
        try:
            self._engine = create_engine(settings.DB_URI, pool_pre_ping=True)
            # Temporary table creation for development purposes
            # In production use Alembic
            Base.metadata.create_all(self._engine)
            self._SessionLocal = sessionmaker(bind=self._engine)
            console_logger.info('Database initialized successfully')

        except SQLAlchemyError as e:
            console_logger.error(f'Database initialization failed: {e}')
            raise e

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        if not self._SessionLocal:
            raise RuntimeError('Database not initialized. Call init() first.')

        session = self._SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            console_logger.error(
                f'Exception while working with a database session: {e}'
            )
            raise e
        finally:
            session.close()


# Global database instance
db = Database()
