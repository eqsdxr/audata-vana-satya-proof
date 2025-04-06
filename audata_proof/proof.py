import os

from audata_proof import exc, handlers
from audata_proof.config import logger, settings
from audata_proof.models.proof_response import ProofResponse


class Proof:
    def __init__(self):
        self.proof_response = ProofResponse(dlp_id=settings.DLP_ID)

    def generate(self) -> ProofResponse:
        logger.info('Starting proof generation')

        input_file_path: str = os.path.join(
            settings.INPUT_DIR, os.listdir(settings.INPUT_DIR)[3]
        )

        # Calculate proof-of-contribution scores: https://docs.vana.org/vana/core-concepts/key-elements/proof-of-contribution/example-implementation
        self.proof_response.ownership = 0
        self.proof_response.quality = 0
        self.proof_response.authenticity = 0  # How authentic is the data is (ie: not tampered with)? (Not implemented here)

        try:
            handlers.check_uniqueness(input_file_path)
            self.proof_response.uniqueness = 1
        # Keep them separate to add different logic in future
        except exc.FingerprintAlreadyExists as e:
            logger.error(e)
            self.proof_response.uniqueness = 0
        except exc.TooSimilarFingerprintAlreadyExists as e:
            logger.error(e)
            self.proof_response.uniqueness = 0

        # Calculate overall score and validity
        self.proof_response.score = 0

        self.proof_response.valid = (
            self.proof_response.ownership == 1
            and self.proof_response.uniqueness == 1
            and self.proof_response.authenticity == 1
            and (self.proof_response.quality > 0.5)
        )

        # Additional (public) properties to include in the proof about the data
        self.proof_response.attributes = {}

        # Additional metadata about the proof, written onchain
        self.proof_response.metadata = {
            'dlp_id': settings.DLP_ID,
        }

        return self.proof_response
