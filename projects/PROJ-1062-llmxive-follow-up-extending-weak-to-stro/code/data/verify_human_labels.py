"""
Verify human labels in the dataset against SC-006 validity criteria.

This script loads the dataset validated in T005.0 (which ensures the
`human_verified_label` field exists) and performs a quality check:
If the field contains nulls or non-boolean values for >5% of the sample,
it raises a ValueError to halt execution.

Dependency: T005.0 (dataset_validation_status.json)
Output: data/processed/human_label_verification.json
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# Attempt to import from the HuggingFace datasets library
# If this fails, the environment setup is incomplete.
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library not found. Please install it via requirements.txt.")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATASET_VALIDATION_FILE = PROCESSED_DIR / "dataset_validation_status.json"
OUTPUT_FILE = PROCESSED_DIR / "human_label_verification.json"

# SC-006 Validity Criteria Threshold
THRESHOLD_FRACTION = 0.05  # 5%

def load_dataset_status() -> Dict[str, Any]:
    """Load the validation status from T005.0."""
    if not DATASET_VALIDATION_FILE.exists():
        raise FileNotFoundError(
            f"Required dependency file not found: {DATASET_VALIDATION_FILE}. "
            "Please run T005.0 (download_aime_verified.py) first."
        )
    with open(DATASET_VALIDATION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_real_dataset() -> Any:
    """
    Load the real HuggingFaceH4/aime_2024 dataset.
    Does NOT support synthetic fallback. If this fails, the run must halt.
    """
    logger.info("Loading real dataset from HuggingFace Hub: HuggingFaceH4/aime_2024...")
    # Use streaming to avoid loading the entire dataset into memory if it's large,
    # but we need to iterate to check labels.
    # We load the 'train' split as per standard AIME usage.
    try:
        dataset = load_dataset(
            "HuggingFaceH4/aime_2024",
            split="train",
            streaming=True
        )
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset from HuggingFace Hub: {e}")
        raise RuntimeError(
            "Real data source unavailable. Cannot proceed without real data. "
            "Do not generate synthetic data."
        ) from e

def verify_labels(dataset: Any) -> Tuple[int, int, bool]:
    """
    Iterate through the dataset and count invalid labels.
    
    Returns:
        Tuple of (total_count, invalid_count, is_valid)
    """
    total_count = 0
    invalid_count = 0
    
    logger.info("Scanning dataset for invalid 'human_verified_label' values...")
    
    # We iterate through the streaming dataset. 
    # To ensure we check a representative sample if the dataset is huge,
    # we could limit to N items, but the task implies checking the "sample" 
    # (which usually means the loaded set). Given memory constraints, 
    # we will check the first 10,000 items or the whole dataset if smaller.
    # However, strict adherence to "verify the dataset" implies checking what we have.
    # We will implement a hard limit on iteration to prevent TLE on massive datasets
    # while still checking a statistically significant sample (N=10k is usually enough 
    # to detect >5% noise if present).
    
    SAMPLE_LIMIT = 10000 
    
    for idx, item in enumerate(dataset):
        if idx >= SAMPLE_LIMIT:
            logger.warning(f"Stopped scanning after {SAMPLE_LIMIT} items. "
                           f"Assuming rest of dataset follows same distribution.")
            break
        
        total_count += 1
        label = item.get("human_verified_label")
        
        # Check for nulls or non-boolean values
        if label is None:
            invalid_count += 1
        elif not isinstance(label, bool):
            # Check if it's a string "True"/"False" that might need casting, 
            # but strict SC-006 usually expects native boolean. 
            # We treat non-native bool as invalid for strictness.
            invalid_count += 1
    
    if total_count == 0:
        raise ValueError("Dataset yielded no items to verify.")
        
    invalid_rate = invalid_count / total_count
    is_valid = invalid_rate <= THRESHOLD_FRACTION
    
    return total_count, invalid_count, is_valid

def main():
    logger.info("Starting T052: Verify Human Labels (SC-006)")
    
    # 1. Check dependency T005.0
    status = load_dataset_status()
    if not status.get("field_exists", False):
        # T005.0 should have already halted if field missing, but double check
        raise RuntimeError("Field 'human_verified_label' is missing. T005.0 should have halted.")
    
    # 2. Load Real Data
    dataset = load_real_dataset()
    
    # 3. Verify Labels
    total, invalid, is_valid = verify_labels(dataset)
    
    # 4. Report and Halt if necessary
    invalid_rate = invalid / total
    
    result = {
        "task_id": "T052",
        "dataset": "HuggingFaceH4/aime_2024",
        "samples_checked": total,
        "invalid_count": invalid,
        "invalid_rate": invalid_rate,
        "threshold": THRESHOLD_FRACTION,
        "is_valid": is_valid,
        "message": "PASSED" if is_valid else f"FAILED: Invalid rate {invalid_rate:.4f} > {THRESHOLD_FRACTION}"
    }
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Verification complete. Result: {result['message']}")
    logger.info(f"Report saved to: {OUTPUT_FILE}")
    
    if not is_valid:
        error_msg = (
            f"SC-006 VALIDATION FAILED. "
            f"Found {invalid} invalid labels ({invalid_rate:.2%}) in {total} samples. "
            f"Threshold: {THRESHOLD_FRACTION:.2%}. "
            "Halting execution as per requirements."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("T052 completed successfully.")

if __name__ == "__main__":
    main()
