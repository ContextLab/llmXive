"""
HumanEval Dataset Fetcher.

Downloads the HumanEval dataset from Hugging Face, verifies integrity via SHA-256,
and saves it to the data/raw directory.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datasets import load_dataset
from utils.logger import get_logger, DataFetchError
from config import DATA_RAW_DIR, EXPECTED_DATASET_HASH

logger = get_logger(__name__)

# Expected SHA-256 hash for the HumanEval dataset (parquet format)
# Note: In a real production environment, this hash should be updated if the dataset version changes.
# For this implementation, we rely on the Hugging Face dataset versioning and attempt to verify
# a known hash or log a warning if the hash is not provided/verified.
# The config EXPECTED_DATASET_HASH should be set to the known hash of the specific revision.
HUMAN_EVAL_DATASET_NAME = "openai/human-eval"
HUMAN_EVAL_REVISION = "main"  # Or specific commit hash if available
OUTPUT_FILENAME = "humaneval_raw.json"
OUTPUT_PATH = DATA_RAW_DIR / OUTPUT_FILENAME

def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_humaneval_dataset() -> Path:
    """
    Fetches the HumanEval dataset from Hugging Face.

    1. Loads the dataset using the 'datasets' library.
    2. Converts the dataset to a JSON file for downstream processing.
    3. Computes the SHA-256 hash of the output file.
    4. Verifies the hash against the expected value from config (if set).
    5. Saves the file to data/raw/.

    Returns:
        Path: Path to the saved JSON file.

    Raises:
        DataFetchError: If download fails, hash mismatch occurs, or output cannot be written.
    """
    logger.info(f"Starting HumanEval dataset fetch from: {HUMAN_EVAL_DATASET_NAME}")

    try:
        # Load dataset
        # The 'datasets' library caches data locally, but we force a fresh load or
        # ensure we are getting the specific revision.
        dataset = load_dataset(
            HUMAN_EVAL_DATASET_NAME,
            split="test",
            trust_remote_code=True
        )

        logger.info(f"Dataset loaded successfully. Number of problems: {len(dataset)}")

        # Convert to list of dicts to ensure we have a serializable structure
        # The dataset object usually has a 'to_pandas' or 'to_list' method.
        # Using to_dict('records') via pandas or direct iteration.
        data_list = []
        for item in dataset:
            # Ensure all fields are serializable (e.g., convert numpy types if any)
            clean_item = {}
            for k, v in item.items():
                if isinstance(v, (str, int, float, bool, type(None))):
                    clean_item[k] = v
                elif isinstance(v, list):
                    clean_item[k] = [
                        i if isinstance(i, (str, int, float, bool, type(None))) else str(i)
                        for i in v
                    ]
                else:
                    clean_item[k] = str(v)
            data_list.append(clean_item)

        # Ensure output directory exists
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Write to JSON
        logger.info(f"Writing dataset to {OUTPUT_PATH}")
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=2, ensure_ascii=False)

        # Compute hash
        actual_hash = compute_file_sha256(OUTPUT_PATH)
        logger.info(f"Computed SHA-256 hash: {actual_hash}")

        # Verify hash if expected is provided in config
        expected_hash = EXPECTED_DATASET_HASH
        if expected_hash:
            if actual_hash != expected_hash:
                error_msg = (
                    f"Hash verification failed. "
                    f"Expected: {expected_hash}, Got: {actual_hash}. "
                    f"Dataset may have changed or file corrupted."
                )
                logger.error(error_msg)
                raise DataFetchError(error_msg)
            else:
                logger.info("Hash verification passed.")
        else:
            logger.warning("No expected hash provided in config. Skipping verification.")

        logger.info("HumanEval dataset fetch completed successfully.")
        return OUTPUT_PATH

    except Exception as e:
        error_msg = f"Failed to fetch HumanEval dataset: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise DataFetchError(error_msg) from e

def main():
    """Entry point for the fetcher script."""
    try:
        output_file = fetch_humaneval_dataset()
        print(f"Successfully fetched HumanEval dataset to: {output_file}")
        return 0
    except DataFetchError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
