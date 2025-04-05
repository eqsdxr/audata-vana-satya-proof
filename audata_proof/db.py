from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from audata_proof.config import settings, logger
from audata_proof.models.db import Base


class Database:
    def __init__(self):
        self._engine = None
        self._SessionLocal = None

    def init(self) -> None:
        try:
            # Get connection string with credentials
            connection_string = settings.DB_URI
            logger.error(connection_string)
            self._engine = create_engine(connection_string, pool_pre_ping=True)
            Base.metadata.create_all(self._engine)
            self._SessionLocal = sessionmaker(bind=self._engine)
            logger.info("Database initialized successfully")

        except SQLAlchemyError as e:
            logger.error(f"Database initialization failed: {e}")
            raise e

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        if not self._SessionLocal:
            raise RuntimeError("Database not initialized. Call init() first.")

        session = self._SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"{e}")
            raise e
        finally:
            session.close()

    def get_session(self) -> Session:
        if not self._SessionLocal:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._SessionLocal()

    def dispose(self) -> None:
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._SessionLocal = None


# Global database instance
db = Database()
