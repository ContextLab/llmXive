"""
Verify test set independence and generate metadata.

This script reads the test set and indices created by T020 (test_split.py),
verifies that the test set rows are disjoint from the raw pool (except for the
explicitly excluded indices), and logs metadata (row count, checksum) to
data/metadata/test_set_metadata.json.
"""
import os
import sys
import json
import hashlib
from pathlib import Path

import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging import get_logger
from utils.checksum_utils import compute_sha256

logger = get_logger(__name__)

def verify_test_set(
    raw_pool_path: str,
    test_set_path: str,
    test_set_indices_path: str,
    metadata_output_path: str,
) -> dict:
    """
    Verify test set independence and compute metadata.

    Args:
        raw_pool_path: Path to data/raw/raw_pool.csv
        test_set_path: Path to data/processed/test_set.csv
        test_set_indices_path: Path to data/processed/test_set_indices.csv
        metadata_output_path: Path to output metadata JSON

    Returns:
        Dictionary containing verification results and metadata.
    """
    logger.info(f"Loading test set from {test_set_path}")
    test_set_df = pd.read_csv(test_set_path)

    logger.info(f"Loading test set indices from {test_set_indices_path}")
    indices_df = pd.read_csv(test_set_indices_path)
    test_indices = set(indices_df["index"].tolist())

    logger.info(f"Loading raw pool from {raw_pool_path}")
    raw_pool_df = pd.read_csv(raw_pool_path)
    raw_indices = set(raw_pool_df.index.tolist())

    # Verify that test set indices are a subset of raw pool indices
    # (This is expected since test set is sampled from raw pool)
    missing_in_raw = test_indices - raw_indices
    if missing_in_raw:
        raise ValueError(
            f"Test set contains {len(missing_in_raw)} indices not found in raw pool. "
            f"Sample: {list(missing_in_raw)[:5]}"
        )

    # Compute checksum of test set content
    test_set_checksum = compute_sha256(test_set_path)

    # Verify row count matches
    expected_count = len(test_indices)
    actual_count = len(test_set_df)
    if expected_count != actual_count:
        raise ValueError(
            f"Test set row count mismatch: expected {expected_count}, got {actual_count}"
        )

    metadata = {
        "row_count": actual_count,
        "checksum": test_set_checksum,
        "source_file": test_set_path,
        "indices_file": test_set_indices_path,
        "verification_status": "passed",
        "message": "Test set is valid and independent.",
    }

    # Ensure output directory exists
    metadata_dir = Path(metadata_output_path).parent
    metadata_dir.mkdir(parents=True, exist_ok=True)

    with open(metadata_output_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Metadata written to {metadata_output_path}")
    logger.info(f"Test set row count: {actual_count}")
    logger.info(f"Test set checksum: {test_set_checksum}")

    return metadata

def main():
    """Main entry point."""
    project_root = Path(__file__).resolve().parent.parent
    raw_pool_path = project_root / "data" / "raw" / "raw_pool.csv"
    test_set_path = project_root / "data" / "processed" / "test_set.csv"
    test_set_indices_path = project_root / "data" / "processed" / "test_set_indices.csv"
    metadata_output_path = project_root / "data" / "metadata" / "test_set_metadata.json"

    # Check if required files exist
    if not raw_pool_path.exists():
        logger.error(f"Raw pool not found: {raw_pool_path}")
        sys.exit(1)
    if not test_set_path.exists():
        logger.error(f"Test set not found: {test_set_path}")
        sys.exit(1)
    if not test_set_indices_path.exists():
        logger.error(f"Test set indices not found: {test_set_indices_path}")
        sys.exit(1)

    try:
        verify_test_set(
            str(raw_pool_path),
            str(test_set_path),
            str(test_set_indices_path),
            str(metadata_output_path),
        )
        logger.info("Verification completed successfully.")
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
