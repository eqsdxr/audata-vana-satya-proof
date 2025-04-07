from loguru import logger as console_logger

from audata_proof.config import settings
from audata_proof.db import Database
from audata_proof.handlers import check_ownership, check_uniqueness
from audata_proof.models.proof_response import ProofResponse


class Proof:
    def __init__(self, db: Database, file_path: str, telegram_id: str):
        self.db = db
        # It is expected that only one file is provided for now
        self.file_path = file_path
        self.telegram_id = telegram_id

        self.proof_response = ProofResponse(dlp_id=settings.DLP_ID)
        # https://docs.vana.org/vana/core-concepts/key-elements/proof-of-contribution/example-implementation
        self.proof_response.ownership = 0
        self.proof_response.quality = 0
        self.proof_response.authenticity = 0  # How authentic is the data is (ie: not tampered with)? (Not implemented here)
        self.proof_response.uniqueness = 0

        self.proof_response.score = 0

        # Additional (public) properties to include in the proof about the data
        self.proof_response.attributes = {}

    def generate(self) -> ProofResponse:
        """Generate proof"""

        console_logger.info('Starting proof generation')

        self.proof_response.ownership = check_ownership(
            self.telegram_id, self.db
        )

        self.proof_response.uniqueness = check_uniqueness(
            self.file_path, self.db
        )

        # Assign validity
        self.proof_response.valid = (
            self.proof_response.ownership == 1
            and self.proof_response.uniqueness == 1
            and self.proof_response.authenticity == 1
            and (self.proof_response.quality > 0.5)
        )

        # Additional metadata about the proof, written onchain
        self.proof_response.metadata = {
            'dlp_id': settings.DLP_ID,
        }

        return self.proof_response
