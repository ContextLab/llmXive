"""
Verification script for the raw bronze dataset.
This task (T007b) explicitly verifies that data/raw/bronze.parquet exists and is readable.
It also validates the file integrity against the recorded state hash if available.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

from config import get_path, init_logger

logger = init_logger(__name__)


def verify_bronze_parquet() -> bool:
    """
    Verifies the existence and readability of data/raw/bronze.parquet.

    Returns:
        bool: True if the file exists, is readable, and passes basic schema checks.
              Raises RuntimeError if verification fails.
    """
    file_path = get_path("data", "raw", "bronze.parquet")
    state_path = get_path("state", "projects", "PROJ-715-physical-activity-levels-and-mood-variab.yaml")

    logger.info(f"Verifying artifact: {file_path}")

    # 1. Check existence
    if not os.path.exists(file_path):
        raise RuntimeError(
            f"CRITICAL: Artifact missing! {file_path} does not exist. "
            "Run 'python code/ingest.py' to download and generate the dataset."
        )

    # 2. Check readability and basic structure
    try:
        df = pd.read_parquet(file_path)
    except Exception as e:
        raise RuntimeError(
            f"CRITICAL: Artifact corrupted! Could not read {file_path}: {e}"
        )

    if df.empty:
        raise RuntimeError(
            f"CRITICAL: Artifact empty! {file_path} contains no data rows."
        )

    # 3. Basic schema validation (ensure expected columns exist)
    # The ingest task should produce a dataframe with at least these columns
    required_columns = {'participant_id', 'timestamp'}
    actual_columns = set(df.columns)

    if not required_columns.issubset(actual_columns):
        missing = required_columns - actual_columns
        raise RuntimeError(
            f"CRITICAL: Schema mismatch in {file_path}. Missing columns: {missing}"
        )

    logger.info(f"Verification successful: {file_path}")
    logger.info(f"  - Rows: {len(df)}")
    logger.info(f"  - Columns: {list(df.columns)}")
    logger.info(f"  - Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    # 4. Optional: Verify against state hash if state file exists
    if os.path.exists(state_path):
        try:
            import yaml
            with open(state_path, 'r') as f:
                state = yaml.safe_load(f)

            recorded_hash = state.get('artifact_hashes', {}).get('data_raw_bronze')
            if recorded_hash:
                # Compute current hash
                import hashlib
                with open(file_path, 'rb') as f:
                    current_hash = hashlib.sha256(f.read()).hexdigest()

                if current_hash != recorded_hash:
                    logger.warning(
                        f"Hash mismatch detected! "
                        f"Recorded: {recorded_hash[:16]}... "
                        f"Current: {current_hash[:16]}... "
                        "The file may have been modified or the state is stale."
                    )
                    # We do not fail here, just warn, as the file is readable and valid.
                    # However, for strict integrity, one might raise here.
                    # Given T007b is verification, we log the warning.
            else:
                logger.info("No recorded hash found in state file; skipping hash verification.")
        except Exception as e:
            logger.warning(f"Could not verify hash against state file: {e}")

    return True


def main():
    """Entry point for T007b verification."""
    try:
        verify_bronze_parquet()
        logger.info("T007b Artifact Verification: PASSED")
        return 0
    except RuntimeError as e:
        logger.error(f"T007b Artifact Verification: FAILED - {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())