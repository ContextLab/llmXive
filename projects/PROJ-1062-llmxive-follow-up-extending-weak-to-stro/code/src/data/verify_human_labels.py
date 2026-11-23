"""
T052: Verify human labels in the dataset against SC-006 validity criteria.

This script explicitly cross-references the `human_verified_label` field in the
loaded dataset against the SC-006 validity criteria.

Requirements:
- If the field is present but contains nulls or non-boolean values for >5% of the sample,
  raise ValueError and halt.
- If the field is missing, the process has already halted in T005.0 (download_aime_verified.py).

Output:
- data/processed/human_label_verification.json: Report of the verification status.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Ensure output directory exists
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# SC-006 Threshold
MAX_NULL_RATIO = 0.05


def load_dataset_status() -> Dict[str, Any]:
    """
    Load the dataset validation status from T005.0.
    Verifies that T005.0 has already run and confirmed the presence of the field.
    """
    status_path = DATA_PROCESSED_DIR / "dataset_validation_status.json"
    if not status_path.exists():
        raise FileNotFoundError(
            f"Dataset validation status file not found at {status_path}. "
            "Please run T005.0 (download_aime_verified.py) first to verify the dataset structure."
        )

    with open(status_path, "r", encoding="utf-8") as f:
        status = json.load(f)

    if not status.get("field_present", False):
        raise RuntimeError(
            "The 'human_verified_label' field was not found in the dataset. "
            "T005.0 should have halted execution. This script assumes the field exists."
        )

    return status


def load_real_dataset() -> List[Dict[str, Any]]:
    """
    Load the real dataset.
    This function assumes the dataset has been downloaded and processed by T005.0
    and is available in a format accessible to this script.
    For this implementation, we assume the dataset is loaded via the HuggingFace datasets
    library or a similar mechanism, and we are verifying the specific field.
    """
    # We need to load the dataset. Since T005.0 fetches HuggingFaceH4/aime_2024,
    # we will fetch it again here to verify the labels.
    # In a real pipeline, we might load from a cached path or a shared object,
    # but for robustness, we re-fetch or load from the expected location.
    # Given the constraint "Real data only", we use the HuggingFace datasets API.
    # We must ensure the dataset is available.

    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is required. Install it via pip install datasets.")
        sys.exit(1)

    logger.info("Loading dataset 'HuggingFaceH4/aime_2024' for label verification...")
    try:
        # Load the dataset in streaming mode to avoid memory issues,
        # though for verification we might need to iterate.
        # We load a small sample first to check structure, then iterate if needed.
        # However, to check the >5% threshold accurately, we need to see the whole dataset
        # or a statistically significant sample. The task says "sample", but for safety
        # we assume we can iterate the full dataset or a large enough subset.
        # Given the dataset size (AIME 2024 is relatively small, ~1000s of problems),
        # we can likely load it into memory.
        dataset = load_dataset("HuggingFaceH4/aime_2024", split="train")
        return list(dataset)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise


def verify_labels(dataset: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify the 'human_verified_label' field against SC-006 criteria.

    Criteria:
    - If the field contains nulls or non-boolean values for >5% of the sample, raise ValueError.

    Args:
        dataset: List of records from the dataset.

    Returns:
        Tuple of (is_valid, stats_dict)
    """
    field_name = "human_verified_label"
    total_count = len(dataset)

    if total_count == 0:
        raise ValueError("Dataset is empty. Cannot verify labels.")

    null_count = 0
    non_boolean_count = 0
    valid_count = 0

    for record in dataset:
        value = record.get(field_name)

        if value is None:
            null_count += 1
        elif not isinstance(value, bool):
            non_boolean_count += 1
        else:
            valid_count += 1

    null_ratio = null_count / total_count
    non_boolean_ratio = non_boolean_count / total_count
    invalid_ratio = null_ratio + non_boolean_ratio

    stats = {
        "total_samples": total_count,
        "valid_count": valid_count,
        "null_count": null_count,
        "non_boolean_count": non_boolean_count,
        "null_ratio": null_ratio,
        "non_boolean_ratio": non_boolean_ratio,
        "invalid_ratio": invalid_ratio,
        "threshold": MAX_NULL_RATIO,
    }

    if invalid_ratio > MAX_NULL_RATIO:
        logger.error(
            f"Verification FAILED. Invalid ratio ({invalid_ratio:.2%}) exceeds threshold ({MAX_NULL_RATIO:.2%})."
        )
        return False, stats

    logger.info(
        f"Verification PASSED. Invalid ratio ({invalid_ratio:.2%}) is within threshold ({MAX_NULL_RATIO:.2%})."
    )
    return True, stats


def main():
    """Main entry point for the verification script."""
    logger.info("Starting human label verification (T052)...")

    # Step 1: Check T005.0 status
    try:
        status = load_dataset_status()
        logger.info(f"Dataset validation status loaded: {status.get('message', 'Unknown')}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Step 2: Load real dataset
    try:
        dataset = load_real_dataset()
        logger.info(f"Loaded {len(dataset)} records from dataset.")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    # Step 3: Verify labels
    is_valid, stats = verify_labels(dataset)

    # Step 4: Save report
    report_path = DATA_PROCESSED_DIR / "human_label_verification.json"
    report = {
        "task_id": "T052",
        "field_name": "human_verified_label",
        "threshold": MAX_NULL_RATIO,
        "passed": is_valid,
        "statistics": stats,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Verification report saved to {report_path}")

    if not is_valid:
        logger.error("Halting execution due to invalid human labels.")
        sys.exit(1)

    logger.info("Human label verification completed successfully.")


if __name__ == "__main__":
    main()