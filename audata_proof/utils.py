from hashlib import md5
import os
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
        _, current_fprint = fingerprint_file(input_file_path)
        new_contribution = Contributions(
            fingerprint=current_fprint,
            fingerprint_hash=md5(str(current_fprint).encode()).hexdigest(),
            file_link=f'https://broken_link{i}.org',
            file_link_hash=md5(str(current_fprint).encode()).hexdigest(),
        )
        with db.session() as session:
            session.add(new_contribution)
            session.commit()
    console_logger.info(
        'Database was successfully seeded'
        'with amount of entities equal to: {}'.format(amount)
    )
