"""
T011a: Verify dataset metadata from HuggingFace.

Fetches dataset info for 'DTS-SN1-15-01-2024' and 'SN18-All-20240204'.
Validates presence of 'substrate_class', 'temperature', and 'solvent' columns.
Raises ValueError if any are missing.
Writes success log to data/processed/schema_check.log.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

REQUIRED_COLUMNS = ['substrate_class', 'temperature', 'solvent']
DATASET_IDS = ['DTS-SN1-15-01-2024', 'SN18-All-20240204']

def setup_schema_check_logger():
    """Setup logger for schema check task."""
    log_dir = Path("data/processed")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "schema_check.log"

    logger = get_logger(
        name="schema_check",
        log_file=log_file,
        level=logging.INFO
    )
    return logger

def fetch_dataset_info(dataset_id: str) -> dict:
    """
    Fetch dataset info from HuggingFace without downloading full data.
    Uses streaming mode to inspect features efficiently.
    """
    try:
        from datasets import load_dataset
        # Load in streaming mode to get info without downloading full data
        ds = load_dataset(dataset_id, split="train", streaming=True)
        
        # Try to get features directly first
        if hasattr(ds, 'features') and ds.features:
            columns = list(ds.features.keys())
        else:
            # Fallback: peek at the first item to infer columns
            # This is necessary if features aren't immediately exposed
            try:
                first_item = next(iter(ds))
                columns = list(first_item.keys())
            except Exception as peek_error:
                raise RuntimeError(f"Failed to inspect dataset {dataset_id}: {peek_error}")
        
        return {
            "dataset_id": dataset_id,
            "columns": columns,
            "success": True
        }
    except Exception as e:
        return {
            "dataset_id": dataset_id,
            "columns": [],
            "success": False,
            "error": str(e)
        }

def validate_columns(dataset_info: dict) -> tuple:
    """
    Validate that all required columns are present in the dataset.
    Returns (is_valid, list_of_missing_columns).
    """
    columns = dataset_info.get("columns", [])
    missing = [col for col in REQUIRED_COLUMNS if col not in columns]
    is_valid = len(missing) == 0
    return is_valid, missing

def main():
    """
    Main entry point for schema check task.
    """
    logger = setup_schema_check_logger()
    logger.info("Starting schema check for SN1 datasets")

    # Ensure output directory exists
    ensure_dirs()

    all_valid = True
    results = []

    for dataset_id in DATASET_IDS:
        logger.info(f"Checking dataset: {dataset_id}")
        info = fetch_dataset_info(dataset_id)
        results.append(info)

        if not info["success"]:
            logger.error(f"Failed to fetch info for {dataset_id}: {info.get('error')}")
            all_valid = False
            continue

        is_valid, missing = validate_columns(info)
        if not is_valid:
            logger.error(f"Dataset {dataset_id} missing required columns: {missing}")
            all_valid = False
        else:
            logger.info(f"Dataset {dataset_id} passed schema validation")

    if not all_valid:
        error_msg = "Schema validation failed. Missing required columns or datasets unavailable."
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("All datasets passed schema validation.")
    logger.info("Schema check completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())