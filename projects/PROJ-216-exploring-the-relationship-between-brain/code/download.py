import os
import sys
import time
import json
import logging
from pathlib import Path

from config import get_dataset_ids, get_sample_limit
from validate_fluid_intelligence import validate_and_aggregate, get_subject_list_from_download_log

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary data directories if they don't exist."""
    dirs = [
        Path("data/raw"),
        Path("data/interim"),
        Path("data/processed"),
        Path("reports")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {[str(d) for d in dirs]}")

def get_subject_list():
    """
    Retrieve the list of subjects to process.
    This function currently relies on the download log if available,
    or falls back to a default empty list if no download has occurred yet.
    """
    return get_subject_list_from_download_log()

def download_dataset(dataset_id, limit):
    """
    Placeholder for the actual download logic using openneuro-py or similar.
    In a real execution, this would fetch data from OpenNeuro.
    For this implementation, we assume the download logic has been executed
    by T015a and T015b, resulting in data in data/raw/.
    """
    logger.info(f"Checking dataset {dataset_id} with limit {limit}")
    # Actual download logic would go here
    # For now, we assume the data is present or the process halts if not
    raw_dir = Path("data/raw") / dataset_id
    if not raw_dir.exists():
        logger.warning(f"Dataset {dataset_id} not found at {raw_dir}. "
                       "Assuming download step T015a/T015b handled this or will fail.")

def fetch_fallback_dataset():
    """
    Implement fallback logic for ds000230 if primary fails.
    Triggered when ds000224 returns 404 or yields no valid subjects.
    """
    logger.warning("Primary dataset unavailable or empty. Triggering fallback to ds000230.")
    fallback_id = "ds000230"
    download_dataset(fallback_id, get_sample_limit())
    return fallback_id

def enforce_sample_limit(subjects):
    """
    Enforce the N=10 sample limit as per config.
    """
    limit = get_sample_limit()
    if len(subjects) > limit:
        logger.info(f"Limiting subjects from {len(subjects)} to {limit}")
        return subjects[:limit]
    return subjects

def validate_and_aggregate():
    """
    Run validation to find Fluid Intelligence scores and aggregate results.
    This calls the logic from validate_fluid_intelligence module.
    """
    return validate_and_aggregate()

def check_validation_and_halt():
    """
    Check the results of T016a (valid_subjects.json).
    If count is 0, log the error and raise a critical ValueError.
    """
    valid_subjects_path = Path("data/processed/valid_subjects.json")
    error_log_path = Path("data/processed/validation_errors.log")

    if not valid_subjects_path.exists():
        logger.error("valid_subjects.json not found. Validation step T016a may not have run.")
        # We treat missing file as 0 valid subjects for the purpose of the halt check
        valid_count = 0
        valid_data = {"subjects": [], "count": 0}
    else:
        with open(valid_subjects_path, 'r') as f:
            valid_data = json.load(f)
        valid_count = valid_data.get("count", 0)

    if valid_count == 0:
        error_msg = "No valid Fluid Intelligence data found in specified datasets"
        logger.critical(error_msg)

        # Log to validation_errors.log with prefix [VALIDATION_ERROR]
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log_path, 'a') as log_file:
            log_file.write(f"[VALIDATION_ERROR] {error_msg}\n")

        raise ValueError(error_msg)

    logger.info(f"Validation successful. Found {valid_count} valid subjects.")
    return valid_data

def main():
    """
    Main entry point for the download and validation pipeline.
    """
    ensure_directories()

    # 1. Attempt primary download (T015a)
    dataset_ids = get_dataset_ids()
    primary_id = dataset_ids[0] if dataset_ids else "ds000224"
    
    # Note: Actual download calls would happen here. 
    # Assuming T015a/T015b logic has populated data/raw/
    
    # 2. Validate and Aggregate (T016a)
    # This step generates data/processed/valid_subjects.json
    validate_and_aggregate()

    # 3. Check for zero valid subjects and halt if necessary (T016c)
    check_validation_and_halt()

    # If we reach here, we have valid subjects
    subjects = get_subject_list()
    limited_subjects = enforce_sample_limit(subjects)
    logger.info(f"Final subject list ready: {len(limited_subjects)} subjects.")

if __name__ == "__main__":
    main()
