from functools import lru_cache
from typing import Literal
from sys import stderr

from loguru import logger

from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure logging
logger.add(
    stderr,
    colorize=True,
    format="<green>{time}</green> <level>{message}</level>",
)


# Configure settings
class Settings(BaseSettings):
    ENV: Literal["local", "staging", "production"]

    DB_HOST_LOCAL: str = "localhost"
    DB_HOST_STAGING: str = "staging-db-host"
    DB_HOST_PRODUCTION: str = "prod-db-host"

    DB_PORT: int = 5432

    DB_NAME_LOCAL: str = "postgres"
    DB_NAME_STAGING: str = "staging_db"
    DB_NAME_PRODUCTION: str = "prod_db"

    DB_PASSWORD_LOCAL: str = "root"
    DB_PASSWORD_STAGING: str = "staging_pwd"
    DB_PASSWORD_PRODUCTION: str = "prod_pwd"

    DB_USER_LOCAL: str = "postgres"
    DB_USER_STAGING: str = "staging_usr"
    DB_USER_PRODUCTION: str = "production_usr"

    @property
    def db_config(self) -> dict:
        env_key = self.ENV.upper()

        return {
            # Use getattr in order to keep code clean
            "HOST": getattr(self, f"DB_HOST_{env_key}"),
            "PORT": self.DB_PORT,
            "DB_NAME": getattr(self, f"DB_NAME_{env_key}"),
            "PASSWORD": getattr(self, f"DB_PASSWORD_{env_key}"),
        }

    @property
    def DB_URI(self) -> str:
        env = self.ENV.upper()
        user = getattr(self, f"DB_USER_{env}")
        password = getattr(self, f"DB_PASSWORD_{env}")
        host = getattr(self, f"DB_HOST_{env}")
        port = self.DB_PORT
        db = getattr(self, f"DB_NAME_{env}")

        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


@lru_cache(maxsize=1)  # Optimize settings getting
def get_settings():
    return Settings()  # type: ignore # Suppress useless warning


settings = get_settings()
