import json
import os
import sys
import traceback

from loguru import logger as console_logger
from audata_proof.config import settings
from audata_proof.proof import Proof


def run() -> None:
    input_files_exist = os.path.isdir(settings.INPUT_DIR) and bool(
        os.listdir(settings.INPUT_DIR)
    )

    if not input_files_exist:
        raise FileNotFoundError(
            f'No input files found in {settings.INPUT_DIR}'
        )

    proof = Proof()
    proof_response = proof.generate()

    output_path = os.path.join(settings.OUTPUT_DIR, 'results.json')
    with open(output_path, 'w') as f:
        json.dump(proof_response.model_dump(), f, indent=2)
    console_logger.info(f'Proof generation complete: {proof_response}')


if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        console_logger.error(f'Error during proof generation: {e}')
        traceback.print_exc()
        sys.exit(1)
