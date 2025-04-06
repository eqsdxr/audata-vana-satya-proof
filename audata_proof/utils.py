import os
from binascii import Error as BinasciiError
from hashlib import md5

from acoustid import fingerprint_file
from loguru import logger as console_logger

from audata_proof.config import settings
from audata_proof.db import db
from audata_proof.models.db import Contributions


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
