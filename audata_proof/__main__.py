import json
import os
import sys
import traceback
from typing import Dict, Any


from audata_proof.proof import Proof
from audata_proof.config import logger
from audata_proof.db import db

INPUT_DIR, OUTPUT_DIR, SEALED_DIR = (
    "/app/demo/input",
    "/app/demo/output",
    "/app/demo/sealed",
)


def load_config() -> Dict[str, Any]:
    """Load proof configuration from environment variables."""
    config = {
        "dlp_id": 1234,  # Set your own DLP ID here
        "use_sealing": os.path.isdir(SEALED_DIR),
        "input_dir": INPUT_DIR,
        "user_email": os.environ.get("USER_EMAIL", None),
    }
    return config


def run() -> None:
    config = load_config()
    input_files_exist = os.path.isdir(INPUT_DIR) and bool(
        os.listdir(INPUT_DIR)
    )

    if not input_files_exist:
        raise FileNotFoundError(f"No input files found in {INPUT_DIR}")

    proof = Proof(config)
    proof_response = proof.generate()

    output_path = os.path.join(OUTPUT_DIR, "results.json")
    with open(output_path, "w") as f:
        json.dump(proof_response.model_dump(), f, indent=2)
    logger.info(f"Proof generation complete: {proof_response}")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.error(f"Error during proof generation: {e}")
        traceback.print_exc()
        sys.exit(1)
