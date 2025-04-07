import json
import os
import zipfile
from binascii import Error as BinasciiError
from hashlib import md5

from acoustid import fingerprint_file
from loguru import logger as console_logger

from audata_proof.config import settings
from audata_proof.db import Database, db
from audata_proof.models.db import Contributions, Users


def seed_db_with_fprints(amount: int):
    """Seed database with fingerprints for testing purposes."""
    db.init()
    for i in range(amount):
        input_file_path: str = os.path.join(
            settings.INPUT_DIR, os.listdir(settings.INPUT_DIR)[i]
        )
        duration, current_fprint = fingerprint_file(input_file_path)
        new_contribution = Contributions(
            fingerprint=current_fprint,
            fingerprint_hash=md5(str(current_fprint).encode()).hexdigest(),
            file_link=f'https://broken_link{i}.org',
            file_link_hash=md5(
                f'https://broken_link{i}.org'.encode()
            ).hexdigest(),
            duration=duration,
        )
        with db.session() as session:
            session.add(new_contribution)
            session.commit()
    console_logger.info(
        'Database was successfully seeded '
        f'with amount of entities equal to: {amount}'
    )


def decode_db_fingerprint(fprint: str):
    try:
        # Decode db fingerprint to be correctly utilized by the comparison func
        db_fingerprint = bytes.fromhex(str(fprint)[2:])
    except BinasciiError as e:
        console_logger.error(f'Error decoding fingerprint from hex: {e}')
        raise BinasciiError()
    return db_fingerprint


def unzip_dir(dir) -> None:
    """
    If the input directory contains any zip files, extract them
    """
    for input_filename in os.listdir(dir):
        input_file = os.path.join(dir, input_filename)

        if zipfile.is_zipfile(input_file):
            with zipfile.ZipFile(input_file, 'r') as zip_ref:
                zip_ref.extractall(dir)


def extract_data(dir) -> tuple:
    ogg_files = []
    user_telegram_id = None

    for filename in os.listdir(dir):
        file_path = os.path.join(dir, filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext == '.json' and filename == 'account.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
                user_telegram_id = data.get('telegram_id')

        elif ext == '.ogg':
            ogg_files.append(file_path)

    if not user_telegram_id or not ogg_files:
        console_logger.error(f'Missing or corrupted files in directory {dir}')
        raise AttributeError()

    return ogg_files, user_telegram_id


def check_user(telegram_id: str, db: Database) -> None:
    """
    Check if a user with this id exists, if not, create one.
    """
    with db.session() as session:
        user = (
            session.query(Users)
            .filter_by(telegram_id=str(telegram_id))
            .one_or_none()
        )

        if not user:
            create_new_user(telegram_id, db)


def create_new_user(telegram_id: str, db: Database) -> None:
    telegram_id = str(telegram_id)
    new_user = Users(telegram_id=telegram_id)
    with db.session() as session:
        session.add(new_user)
        session.commit()
    console_logger.info(f'New user with id {telegram_id} created')
