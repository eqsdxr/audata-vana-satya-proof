from functools import lru_cache
from sys import stderr
from typing import Literal

from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure logging
logger.add(
    stderr,
    colorize=True,
    format='<green>{time}</green> <level>{message}</level>',
)


# Configure settings
class Settings(BaseSettings):
    ENV_: Literal['local', 'staging', 'production']

    DLP_ID: int = 1234
    USE_SEALING: str = '/app/demo/sealed'
    INPUT_DIR: str = '/app/demo/input'
    USER_EMAIL: str | None = None
    OUTPUT_DIR: str = '/app/demo/output'

    # Database environment variables

    DB_HOST_LOCAL: str = 'localhost'
    DB_HOST_STAGING: str = 'staging-db-host'
    DB_HOST_PRODUCTION: str = 'prod-db-host'

    DB_PORT: int = 5432

    DB_NAME_LOCAL: str = 'postgres'
    DB_NAME_STAGING: str = 'staging_db'
    DB_NAME_PRODUCTION: str = 'prod_db'

    DB_PASSWORD_LOCAL: str = 'root'
    DB_PASSWORD_STAGING: str = 'staging_pwd'
    DB_PASSWORD_PRODUCTION: str = 'prod_pwd'

    DB_USER_LOCAL: str = 'postgres'
    DB_USER_STAGING: str = 'staging_usr'
    DB_USER_PRODUCTION: str = 'production_usr'

    @property
    def DB_URI(self) -> str:
        env = self.ENV_.upper()

        user = getattr(self, f'DB_USER_{env}')
        password = getattr(self, f'DB_PASSWORD_{env}')
        host = getattr(self, f'DB_HOST_{env}')
        port = self.DB_PORT
        db = getattr(self, f'DB_NAME_{env}')

        return f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'

    # Settings class configuration
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', case_sensitive=True
    )


@lru_cache(maxsize=1)  # Optimize settings getting
def get_settings():
    return Settings()  # type: ignore # Suppress useless warning


settings = get_settings()
