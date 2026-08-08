import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_dataset_ids, get_sample_limit
from validate_fluid_intelligence import validate_and_aggregate

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_subject_list(dataset_dir: Path) -> List[str]:
    """
    Retrieve a list of subject IDs from the dataset directory.
    Assumes standard BIDS structure (sub-<label>/).
    """
    subjects = []
    if not dataset_dir.exists():
        logger.warning(f"Dataset directory does not exist: {dataset_dir}")
        return subjects
    
    for item in dataset_dir.iterdir():
        if item.is_dir() and item.name.startswith('sub-'):
            subjects.append(item.name)
    
    return sorted(subjects)

def download_dataset(dataset_id: str, target_dir: Path) -> bool:
    """
    Download dataset from OpenNeuro.
    In a real implementation, this would use openneuro-py or similar.
    For this pipeline, we assume the data is already downloaded to data/raw/{dataset_id}.
    Returns True if data appears to be present, False otherwise.
    """
    # Check if data directory exists (simulating a successful download check)
    data_path = target_dir / dataset_id
    if data_path.exists() and any(data_path.iterdir()):
        logger.info(f"Dataset {dataset_id} found at {data_path}")
        return True
    
    logger.error(f"Dataset {dataset_id} not found at {data_path}. "
                 "Please ensure data is downloaded to data/raw/")
    return False

def enforce_sample_limit(subjects: List[str], limit: int) -> List[str]:
    """
    Enforce the sample limit (N=10) on the subject list.
    """
    if len(subjects) <= limit:
        return subjects
    return subjects[:limit]

def validate_and_aggregate(data_dir: Path, output_dir: Path, limit: int) -> Dict[str, Any]:
    """
    Validate subjects for Fluid Intelligence scores and aggregate results.
    This function calls the validation logic and handles the zero-subject case.
    
    Args:
        data_dir: Root directory containing downloaded datasets
        output_dir: Directory to write validation results
        limit: Maximum number of subjects to process
    
    Returns:
        Dictionary with validation results
    
    Raises:
        ValueError: If no valid subjects with Fluid Intelligence scores are found
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get dataset IDs from config
    dataset_ids = get_dataset_ids()
    
    all_subjects = []
    
    for ds_id in dataset_ids:
        ds_path = data_dir / ds_id
        if ds_path.exists():
            subjects = get_subject_list(ds_path)
            logger.info(f"Found {len(subjects)} subjects in {ds_id}")
            all_subjects.extend(subjects)
        else:
            logger.warning(f"Dataset {ds_id} not found, skipping")
    
    if not all_subjects:
        # If no subjects found at all, we can't validate
        error_msg = "No valid Fluid Intelligence data found in specified datasets"
        logger.critical(error_msg)
        _log_pipeline_error(error_msg, data_dir / "processed" / "pipeline_errors.log")
        raise ValueError(error_msg)
    
    # Enforce sample limit
    limited_subjects = enforce_sample_limit(all_subjects, limit)
    logger.info(f"Applying sample limit: {len(limited_subjects)} subjects")
    
    # Validate subjects for Fluid Intelligence
    validation_result = validate_and_aggregate(
        data_dir, 
        output_dir / "valid_subjects.json", 
        limited_subjects
    )
    
    count = validation_result.get("count", 0)
    
    if count == 0:
        error_msg = "No valid Fluid Intelligence data found in specified datasets"
        logger.critical(error_msg)
        _log_pipeline_error(error_msg, output_dir / "pipeline_errors.log")
        raise ValueError(error_msg)
    
    logger.info(f"Validation complete: {count} valid subjects found")
    return validation_result

def _log_pipeline_error(error_message: str, log_path: Path) -> None:
    """
    Log a critical pipeline error to the pipeline_errors.log file.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_path, 'a') as f:
        f.write(f"[{timestamp}] CRITICAL: {error_message}\n")
    
    logger.error(f"Error logged to {log_path}")

def main():
    """
    Main entry point for the download and validation pipeline.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    # Ensure processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        result = validate_and_aggregate(data_dir, processed_dir, get_sample_limit())
        print(json.dumps(result, indent=2))
    except ValueError as e:
        # Re-raise to allow pytest to catch it with the exact message
        print(f"Critical Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during download/validation")
        sys.exit(1)

if __name__ == "__main__":
    main()
