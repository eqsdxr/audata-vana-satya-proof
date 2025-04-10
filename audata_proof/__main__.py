import json
import os
import sys
import traceback

from loguru import logger as console_logger

from audata_proof.config import settings
from audata_proof.db import db
from audata_proof.proof import Proof
from audata_proof.utils import check_user, extract_data, unzip_dir


def run() -> None:
    input_files_exist = os.path.isdir(settings.INPUT_DIR) and bool(
        os.listdir(settings.INPUT_DIR)
    )

    if not input_files_exist:
        raise FileNotFoundError(
            f'No input files found in {settings.INPUT_DIR}'
        )

    unzip_dir(settings.INPUT_DIR)

    ogg_files, telegram_id = extract_data(settings.INPUT_DIR)

    # Init single db session which will be passed into all handlers
    # It is generally recommended to do it this way to avoid
    # excessive inits in functions which also turns to be kind of chaotic
    db.init()

    # Make sure user exists or create one
    check_user(telegram_id, db)

    proof = Proof(db, ogg_files[0], telegram_id)
    proof_response = proof.generate()

    output_path = os.path.join(settings.OUTPUT_DIR, 'results.json')
    #with open(output_path, 'w') as f:
        #json.dump(proof_response.model_dump(), f, indent=2)
    console_logger.info(f'Proof generation complete: {proof_response}')


if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        console_logger.error(f'Error during proof generation: {e}')
        traceback.print_exc()
        sys.exit(1)
