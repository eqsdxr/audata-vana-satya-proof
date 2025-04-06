from hashlib import md5
from acoustid import fingerprint_file, compare_fingerprints

from loguru import logger as console_logger
from audata_proof.db import Database
from audata_proof.exc import (
    FingerprintAlreadyExists,
    TooSimilarFingerprintAlreadyExists,
)
from audata_proof.models.db import Contributions


def check_uniqueness(
    file_path: str,
    db: Database,
    similarity_threshold: float = 0.8,
    yield_per: int = 5,
) -> None:
    """
    Check fingerprint for uniqueness.

    Parameters
    ----------
    file_path : str
        Path to the fingerprint file.
    db: Database
        Database object.
    similarity_threshold : float, optional
        Threshold above which a fingerprint is considered too
        similar, by default it's 0.8.
    yield_per: int, optional
        Amount of entities loaded into memory while comparing
        fingerprints.

    Returns
    -------
    None
        No value is returned. Control flow is managed using
        try-except constructions, and exceptions are raised
        if conditions for uniqueness are violated. It is made
        in this way for the sake of simple mechanism of
        returning different error messages to a user.

    Raises
    ------
    FingerprintAlreadyExists
        If a fingerprint with the same hash exists in the
        database.
    TooSimilarFingerprintAlreadyExists
        If a fingerprint exceeds the similarity threshold.
    MultipleResultsFound
        If multiple fingerprints with the same hash exists
        in the database.
    """
    # Check function's input
    if not 0.0 <= similarity_threshold <= 1.0:
        raise ValueError('similarity_threshold must be between 0.0 and 1.0')
    if yield_per < 1:
        raise ValueError('yield_per must be >= 1')

    # Get fingerprint and duration
    current_duration, current_fprint = fingerprint_file(file_path)

    # Hash current fprint
    current_fprint_hash = md5(str(current_fprint).encode()).hexdigest()

    with db.session() as session:
        # Check for exactly the same one, if more than one - raise exception
        duplicate = (
            session.query(Contributions)
            .filter_by(fingerprint_hash=current_fprint_hash)
            .one_or_none()
        )
        if duplicate:
            console_logger.info(
                'Exact fingerprint match found:\n'
                f'Current fingerprint: {current_fprint}\n'
                f'Hash of current fingerprint: {current_fprint_hash}\n'
                f'Fingerprint in DB: {duplicate.fingerprint}\n'
                f'Hash of fingerprint in DB: {duplicate.fingerprint_hash}'
            )
            raise FingerprintAlreadyExists(f'Hash: {current_fprint_hash}')

        # Loop through db fingerprints and compare for similarity
        # Use yield_per to avoid loading all db in memory
        for contribution in session.query(Contributions).yield_per(yield_per):
            # Provide arguments in format (duration, fingerprint)
            # `similarity_score` is guaranteed to be between 0.0 and 1.0
            similarity_score = compare_fingerprints(
                (current_duration, current_fprint),
                (contribution.duration, contribution.fingerprint),
            )

            if similarity_score >= similarity_threshold:
                console_logger.info(
                    f'Similar fingerprint found (similarity score: {similarity_score}):\n'
                    f'Current: {current_fprint}\n'
                    f'Hash of current: {current_fprint_hash}\n'
                    f'Existing: {contribution.fingerprint}\n'
                    f'Hash of existing: {contribution.fingerprint_hash}\n'
                )
                raise TooSimilarFingerprintAlreadyExists()
