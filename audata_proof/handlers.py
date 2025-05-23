from hashlib import md5
from typing import Literal

import numpy as np
import torch
import librosa
import yaml
from acoustid import compare_fingerprints, fingerprint_file
from loguru import logger as console_logger
from speechmos import dnsmos

from audata_proof.config import settings
from audata_proof.db import Database
from audata_proof.model.model import RawNet
from audata_proof.schemas.db import Contributions, Users
from audata_proof.utils import decode_db_fingerprint, pad, process_audio


def check_uniqueness(
    file_path: str,
    db: Database,
    similarity_threshold: float = 0.8,
    yield_per: int = 5,
) -> Literal[0, 1]:
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
    1 if it's unique
    0 if not

    Raises
    ------
    TypeError
        if type of fingerprints were incorrect while
        comparing.
    Exception
        If there is an unexpected error occured.
    """
    # Check the function's input
    if not 0.0 <= similarity_threshold <= 1.0:
        raise ValueError('similarity_threshold must be between 0.0 and 1.0')
    if yield_per < 1:
        raise ValueError('yield_per must be >= 1')

    # Get fingerprint, duration, and hash
    current_duration, current_fprint = fingerprint_file(file_path)
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
            return 0

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
                # If the exception is raised check types and values of
                # variables that compare_fingerprints function gets
                console_logger.error(
                    f'Type error in comparison: {e}'
                    f'Current one: {current_fprint}\n'
                    f'Hash of current one: {current_fprint_hash}\n'
                    f'Existing one: {db_fprint}\n'
                    f'Hash of existing one: {db_fprint}\n'
                )
                raise
            # For debugging purposes
            except Exception as e:
                console_logger.error(
                    f'Unexpected error while comparing fingerprints: {e}'
                    f'Current one: {current_fprint}\n'
                    f'Hash of current one: {current_fprint_hash}\n'
                    f'Existing one: {db_fprint}\n'
                    f'Hash of existing one: {db_fprint}\n'
                )
                raise

            if similarity_score >= similarity_threshold:
                console_logger.info(
                    f'Similar fingerprint found (similarity score: {similarity_score}):\n'
                    f'Current: {current_fprint}\n'
                    f'Hash of current: {current_fprint_hash}\n'
                    f'Existing: {db_fprint}\n'
                    f'Hash of existing: {db_fprint}\n'
                )
                return 0
    # All checks are passed
    return 1


def check_ownership(telegram_id: str, db: Database) -> Literal[0, 1]:
    """
    A user is considered to pass ownership test unless they have been banned.
    If the user doesn't exist, they're initialized and granted ownership.

    Returns
    -------
        1 if user has not been banned
        0 if banned
    """
    with db.session() as session:
        user = (
            session.query(Users).filter_by(telegram_id=str(telegram_id)).one()
        )

        return 0 if user.is_banned else 1  # type: ignore


def check_authenticity(file_path: str) -> Literal[0, 1]:
    with open(settings.path_to_yaml, 'r') as f:
        config = yaml.safe_load(f)

    device = torch.device('cpu')

    model = RawNet(config['model'], device=device)
    model.load_state_dict(
        torch.load(
            settings.path_to_model, map_location='cpu', weights_only=False
        )
    )
    model.eval()
    model = model.to(device)

    y, _ = process_audio(file_path)

    segments = []
    max_len = 96000
    total_len = len(y)

    if total_len <= max_len:
        y_pad = pad(y, max_len)
        segments.append(torch.tensor(y_pad, dtype=torch.float32))
    else:
        num_chunks = total_len // max_len
        for i in range(num_chunks):
            seg = y[i * max_len : (i + 1) * max_len]
            segments.append(
                torch.tensor(pad(seg, max_len), dtype=torch.float32)
            )

    model.eval()
    probs = []
    with torch.no_grad():
        for segment in segments:
            input_tensor = segment.unsqueeze(0).to(device)
            output = model(input_tensor)
            if isinstance(output, tuple):
                output = output[0]
            softmax_out = torch.softmax(output, dim=1)[0][1].item()
            probs.append(softmax_out)

    final_prob = float(np.mean(probs))
    print('Likely Real' if final_prob > 0.5 else 'Likely Fake')
    print(f'Score: {final_prob}')
    return 1 if final_prob > 0.5 else 0




class Quality:
    def __init__(self, target_sr=16000, max_duration=120.0) -> None:
        self.target_sr = target_sr
        self.max_duration = max_duration

    def load_audio(self, file_path: str):
        amplitudes, _ = librosa.load(
            file_path, sr=self.target_sr
        )  # for dnsmos we need sr=16000
        signal = librosa.util.normalize(amplitudes)

        return signal

    def get_p835_metrics(self, amplitudes):
        result = dnsmos.run(amplitudes, sr=self.target_sr)
        del result["p808_mos"]  # delete P.808 metric # type: ignore

        mos_mean = np.mean([float(i) for i in result.values()]) * 2 / 10 #type: ignore

        return mos_mean

    def get_duration_score(self, duration, max_duration=120.0):
        duration_score = min(duration / max_duration, 1.0)

        return duration_score

    def check_quality(self, file_path):
        try:
            y = self.load_audio(file_path)

        except FileNotFoundError:  # if filename is incorrect or file not found
            console_logger.error("File not found!")
            return

        sig_score = self.get_p835_metrics(y)

        return sig_score
