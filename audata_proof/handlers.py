from acoustid import fingerprint_file

from audata_proof.config import logger
from audata_proof.db import db
from audata_proof.exc import (
    FingerprintAlreadyExists,
    TooSimilarFingerprintAlreadyExists,
)
from audata_proof.models.db import Contributions


def check_uniqueness(file_path: str, similarity_threshold: float = 0.8):
    current_duration, current_fprint = fingerprint_file(
        file_path
    )  # getting fingerprint
    db.init()
    with db.session() as session:
        # Check for exactly the same one
        duplicate = (
            session.query(Contributions)
            .filter_by(fingerprint=str(current_fprint))
            .one_or_none()
        )
        if duplicate:
            logger.info(
                'Exact fingerprint match found: {} {}'.format(
                    current_fprint, duplicate.fingerprint
                )
            )
            raise FingerprintAlreadyExists()

        # Loop through db fingerprints and compare
        for contribution in session.query(Contributions).all():
            similarity_score = 0.4  # compare_fingerprints(
            #    (current_duration, current_fprint), (contribution.duration, contribution.fingerprint))
            # )

            if similarity_score >= similarity_threshold:
                logger.info(
                    f'Similar fingerprint found (Score: {similarity_score}): {current_fprint} and {contribution.fingerprint}'
                )
                raise TooSimilarFingerprintAlreadyExists()
