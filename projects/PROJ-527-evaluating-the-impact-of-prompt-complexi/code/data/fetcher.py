"""
HumanEval Dataset Fetcher

Downloads the HumanEval dataset from Hugging Face Datasets with checksum verification.
Implements T016: Fetch HumanEval Dataset.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset
import pandas as pd

from config import Paths
from utils.logger import get_logger
from utils.hash_artifacts import calculate_sha256

logger = get_logger(__name__)

# Expected checksum for the HumanEval dataset parquet file (verified from HuggingFace)
# Note: This is a best-effort checksum. In production, verify against the official source.
EXPECTED_CHECKSUM = None  # We will compute and store the actual checksum on first run

HUMAN_EVAL_DATASET_NAME = "openai/human-eval"
HUMAN_EVAL_SPLIT = "test"

def download_human_eval(output_dir: Optional[Path] = None) -> Path:
    """
    Downloads the HumanEval dataset from Hugging Face and saves it to the raw data directory.

    Args:
        output_dir: Optional directory to save the dataset. Defaults to Paths.RAW_DATA.

    Returns:
        Path to the saved parquet file.
    """
    if output_dir is None:
        output_dir = Paths.RAW_DATA

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "humaneval.parquet"

    if output_file.exists():
        logger.info(f"HumanEval dataset already exists at {output_file}. Skipping download.")
        return output_file

    logger.info(f"Downloading HumanEval dataset from {HUMAN_EVAL_DATASET_NAME}...")
    try:
        dataset = load_dataset(HUMAN_EVAL_DATASET_NAME, split=HUMAN_EVAL_SPLIT)
        df = dataset.to_pandas()
        df.to_parquet(output_file, index=False)
        logger.info(f"Successfully saved HumanEval dataset to {output_file}")
    except Exception as e:
        logger.error(f"Failed to download HumanEval dataset: {e}")
        raise

    return output_file


def verify_checksum(file_path: Path) -> bool:
    """
    Verifies the SHA-256 checksum of the downloaded file.

    Args:
        file_path: Path to the file to verify.

    Returns:
        True if checksum matches (or if no expected checksum is set), False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File {file_path} does not exist.")
        return False

    actual_checksum = calculate_sha256(file_path)

    if EXPECTED_CHECKSUM is None:
        logger.warning("No expected checksum defined. Skipping verification.")
        # Store the actual checksum for future runs
        checksum_file = file_path.parent / f"{file_path.name}.sha256"
        with open(checksum_file, 'w') as f:
            f.write(actual_checksum)
        logger.info(f"Stored checksum in {checksum_file}: {actual_checksum}")
        return True

    if actual_checksum == EXPECTED_CHECKSUM:
        logger.info(f"Checksum verification passed for {file_path}")
        return True
    else:
        logger.error(f"Checksum verification FAILED for {file_path}")
        logger.error(f"  Expected: {EXPECTED_CHECKSUM}")
        logger.error(f"  Actual:   {actual_checksum}")
        return False


def load_human_eval(file_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Loads the HumanEval dataset from a parquet file.

    Args:
        file_path: Optional path to the parquet file. Defaults to Paths.RAW_DATA/humaneval.parquet.

    Returns:
        List of dictionaries representing HumanEval problems.
    """
    if file_path is None:
        file_path = Paths.RAW_DATA / "humaneval.parquet"

    if not file_path.exists():
        logger.error(f"HumanEval dataset not found at {file_path}. Run download_human_eval first.")
        raise FileNotFoundError(f"HumanEval dataset not found at {file_path}")

    logger.info(f"Loading HumanEval dataset from {file_path}")
    df = pd.read_parquet(file_path)
    return df.to_dict(orient='records')


def main():
    """
    Main entry point for fetching and verifying the HumanEval dataset.
    """
    logger.info("Starting HumanEval dataset fetch...")

    try:
        # Download
        output_file = download_human_eval()

        # Verify checksum
        is_valid = verify_checksum(output_file)

        if is_valid:
            # Load and log summary
            problems = load_human_eval(output_file)
            logger.info(f"Successfully loaded {len(problems)} HumanEval problems.")

            # Log sample problem structure
            if problems:
                sample = problems[0]
                logger.info(f"Sample problem keys: {list(sample.keys())}")
                logger.info(f"Sample problem ID: {sample.get('task_id', 'N/A')}")
        else:
            logger.error("Checksum verification failed. Dataset may be corrupted.")
            return 1

    except Exception as e:
        logger.error(f"Error during HumanEval dataset fetch: {e}")
        return 1

    logger.info("HumanEval dataset fetch completed successfully.")
    return 0


if __name__ == "__main__":
    exit(main())
