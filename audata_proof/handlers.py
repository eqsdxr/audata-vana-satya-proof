from hashlib import md5

from acoustid import compare_fingerprints, fingerprint_file
from loguru import logger as console_logger

from audata_proof.db import Database
from audata_proof.exc import (
    FingerprintAlreadyExists,
    FingerprintComparisonTypeError,
    TooSimilarFingerprintAlreadyExists,
)
from audata_proof.models.db import Contributions
from audata_proof.utils import decode_db_fingerprint


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
    FingerprintComparisonTypeError
        if type of fingerprints were incorrect while
        comparing.
    TooSimilarFingerprintAlreadyExists
        If a fingerprint exceeds the similarity threshold.
    MultipleResultsFound
        If multiple fingerprints with the same hash exists
        in the database.
    Exception
        If there is an unexpected error occured.
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
                f'Fingerprint in DB: {decode_db_fingerprint(str(duplicate.fingerprint))}\n'
                f'Hash of fingerprint in DB: {duplicate.fingerprint_hash}'
            )
            raise FingerprintAlreadyExists(f'Hash: {current_fprint_hash}')

        # Loop through db fingerprints and compare for similarity
        # Use yield_per to avoid loading all db in memory
        for contribution in session.query(Contributions).yield_per(yield_per):
            # Decode db fingerprint
            db_fprint = decode_db_fingerprint(str(contribution.fingerprint))

            try:
                # Provide arguments in format (duration, fingerprint)
                # `similarity_score` is guaranteed to be between 0.0 and 1.0
                similarity_score = compare_fingerprints(
                    (current_duration, current_fprint),
                    (contribution.duration, db_fprint),
                )
            except TypeError as e:
                console_logger.error(
                    f'Type error in comparison: {e}'
                    f'Current one: {current_fprint}\n'
                    f'Hash of current one: {current_fprint_hash}\n'
                    f'Existing one: {db_fprint}\n'
                    f'Hash of existing one: {db_fprint}\n'
                )
                raise FingerprintComparisonTypeError()
            # For debugging purposes
            except Exception as e:
                console_logger.error(
                    f'Unexpected error while comparing fingerprints: {e}'
                    f'Current one: {current_fprint}\n'
                    f'Hash of current one: {current_fprint_hash}\n'
                    f'Existing one: {db_fprint}\n'
                    f'Hash of existing one: {db_fprint}\n'
                )
                raise e

            if similarity_score >= similarity_threshold:
                console_logger.info(
                    f'Similar fingerprint found (similarity score: {similarity_score}):\n'
                    f'Current: {current_fprint}\n'
                    f'Hash of current: {current_fprint_hash}\n'
                    f'Existing: {db_fprint}\n'
                    f'Hash of existing: {db_fprint}\n'
                )
                raise TooSimilarFingerprintAlreadyExists()
