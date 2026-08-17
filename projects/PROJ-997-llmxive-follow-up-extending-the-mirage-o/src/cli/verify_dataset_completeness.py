"""
T015e: Verify dataset completeness against expected counts.

Loads the generated training_sample.parquet and compares the row count
against the expected count after skips (tracked during generation in T015b).

Behavior:
- Logs a warning if counts do not match due to T013 skips (transient failures).
- Does NOT fail loudly unless the count falls below the n=300 floor (SC-005).
- Reads the expected count from the generation metadata file if available,
  otherwise attempts to infer from the generation log or defaults to a check
  against a known minimum.

Dependency: Must run after T015 (generate_dataset.py).
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

# Import shared logging config
from src.config.logging_config import setup_logger, ensure_log_dir

# Constants
MIN_SAMPLE_FLOOR = 300
DATASET_PATH = "data/processed/training_sample.parquet"
METADATA_PATH = "data/processed/generation_metadata.json"
LOG_PATH = "logs/pipeline.log"


def load_generation_metadata(metadata_path: Path) -> Optional[dict]:
    """
    Load the generation metadata file if it exists.
    Returns None if file is missing or invalid JSON.
    """
    if not metadata_path.exists():
        logging.warning(f"Metadata file not found at {metadata_path}. "
                        "Cannot verify against expected count from metadata.")
        return None

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse generation metadata: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error reading metadata: {e}")
        return None


def verify_dataset_completeness(
    dataset_path: Path,
    metadata_path: Path,
    min_floor: int = MIN_SAMPLE_FLOOR
) -> Tuple[bool, str]:
    """
    Verify the dataset completeness.

    Args:
        dataset_path: Path to the training_sample.parquet file.
        metadata_path: Path to the generation_metadata.json file.
        min_floor: Minimum number of samples required (SC-005).

    Returns:
        Tuple of (success: bool, message: str).
        success is False only if the sample count is below the floor.
    """
    # 1. Load the dataset
    if not dataset_path.exists():
        return False, f"Dataset file not found at {dataset_path}. " \
                      "Ensure T015 (generate_dataset.py) has run successfully."

    try:
        df = pd.read_parquet(dataset_path)
    except Exception as e:
        return False, f"Failed to load dataset from {dataset_path}: {e}"

    actual_count = len(df)
    logging.info(f"Loaded dataset from {dataset_path}. Row count: {actual_count}")

    # 2. Check minimum floor first (SC-005)
    if actual_count < min_floor:
        msg = (f"CRITICAL: Dataset row count ({actual_count}) is below the "
               f"minimum floor of {min_floor} (SC-005). "
               f"The run did not produce enough valid samples.")
        logging.error(msg)
        return False, msg

    # 3. Check against expected count if metadata is available
    metadata = load_generation_metadata(metadata_path)
    if metadata:
        expected_count = metadata.get("expected_count_after_skips")
        if expected_count is not None:
            if actual_count != expected_count:
                # This is a warning, not a failure, unless it's below floor (checked above)
                diff = expected_count - actual_count
                reason = "unknown"
                if diff > 0:
                    reason = "more samples were skipped during generation than expected"
                else:
                    reason = "more samples were processed than expected (unexpected)"

                msg = (f"WARNING: Actual row count ({actual_count}) does not match "
                       f"expected count from metadata ({expected_count}). "
                       f"Difference: {diff}. Reason: {reason}. "
                       f"This may indicate transient T013 skips or metadata mismatch.")
                logging.warning(msg)
            else:
                logging.info(f"Row count ({actual_count}) matches expected count from metadata.")
        else:
            logging.info("Metadata exists but 'expected_count_after_skips' field is missing.")
    else:
        logging.info("No generation metadata found to compare against. "
                     f"Verified only against minimum floor ({min_floor}).")

    # 4. Final verdict
    if actual_count >= min_floor:
        return True, f"Dataset completeness verified. Count: {actual_count} (>= {min_floor})."
    else:
        # Should be caught by step 2, but for safety
        return False, f"Dataset count {actual_count} is below floor {min_floor}."


def main():
    """Entry point for T015e."""
    parser = argparse.ArgumentParser(description="Verify dataset completeness (T015e)")
    parser.add_argument(
        "--dataset",
        type=str,
        default=DATASET_PATH,
        help=f"Path to the training_sample.parquet file (default: {DATASET_PATH})"
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default=METADATA_PATH,
        help=f"Path to the generation_metadata.json file (default: {METADATA_PATH})"
    )
    parser.add_argument(
        "--min-floor",
        type=int,
        default=MIN_SAMPLE_FLOOR,
        help=f"Minimum sample count required (default: {MIN_SAMPLE_FLOOR})"
    )

    args = parser.parse_args()

    # Setup logging
    ensure_log_dir(LOG_PATH)
    logger = setup_logger(LOG_PATH)
    logger.info("Starting T015e: Verify Dataset Completeness")

    dataset_path = Path(args.dataset)
    metadata_path = Path(args.metadata)
    min_floor = args.min_floor

    success, message = verify_dataset_completeness(
        dataset_path, metadata_path, min_floor
    )

    if success:
        logger.info(f"Verification PASSED: {message}")
        print(message)
        sys.exit(0)
    else:
        logger.error(f"Verification FAILED: {message}")
        print(message, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
