from loguru import logger as console_logger

from audata_proof.db import Database
from audata_proof.models.db import Users


def init_new_user(telegram_id: str, db: Database) -> None:
    telegram_id = str(telegram_id)
    new_user = Users(telegram_id=telegram_id)
    with db.session() as session:
        session.add(new_user)
        session.commit()
    console_logger.info(f'New user with id {telegram_id} created')
