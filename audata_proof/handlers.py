from acoustid import fingerprint_file, compare_fingerprints

from audata_proof.db import db
from audata_proof.exc import (
    FingerprintAlreadyExists,
    TooSimilarFingerprintAlreadyExists,
)
from audata_proof.models.db import Contributions
from audata_proof.config import logger


class Uniqueness:
    def __call__(self, file_path: str, similarity_threshold: float = 0.8):
        # Get the fingerprint of the input file
        current_fprint, _ = fingerprint_file(file_path)

        with db.session() as session:
            # Check for exactly the same one
            duplicate = (
                session.query(Contributions)
                .filter_by(fingerprint=current_fprint)
                .first()
            )
            if duplicate:
                logger.info(
                    "Exact fingerprint match found: {} {}".format(
                        current_fprint, duplicate
                    )
                )
                raise FingerprintAlreadyExists()

            # Loop through db fingerprints and compare
            for db_fprint in session.query(Contributions).all():
                fprint2 = db_fprint.fingerprint
                similarity_score = compare_fingerprints(
                    current_fprint, fprint2
                )

                if similarity_score >= similarity_threshold:
                    logger.info(
                        f"Similar fingerprint found (Score: {similarity_score}): {current_fprint} and {fprint2}"
                    )
                    raise TooSimilarFingerprintAlreadyExists()
