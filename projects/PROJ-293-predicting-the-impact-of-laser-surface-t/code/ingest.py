import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

from logging_config import setup_logging, get_logger, raise_on_missing_data
from hygiene import calculate_md5, update_artifact_hash, save_artifact_hashes

# Initialize logger
logger = get_logger(__name__)

# Constants for paths
DATA_PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")
RECORD_COUNTS_PATH = DATA_PROCESSED_DIR / "record_counts.json"
THRESHOLD_CHECK_PATH = DATA_PROCESSED_DIR / "threshold_check.json"
PRE_CHECK_PATH = REPORTS_DIR / "pre_check.json"

def count_records(input_file: Optional[Path] = None) -> Dict[str, int]:
    """
    Calculate total record count, split into normalized_count and raw_count.
    
    Reads 'data/processed/aggregated_clean.csv' (produced by T013c) which must contain
    the 'normalization_method' column.
    
    Args:
        input_file: Optional path to the input CSV. Defaults to AGGREGATED_CLEAN_PATH.
        
    Returns:
        Dict with keys: 'normalized_count', 'raw_count', 'total_count'.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the 'normalization_method' column is missing.
    """
    input_file = Path(input_file) if input_file else DATA_PROCESSED_DIR / "aggregated_clean.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
        
    logger.info(f"Reading input file: {input_file}")
    df = pd.read_csv(input_file)
    
    if 'normalization_method' not in df.columns:
        raise ValueError(
            f"Missing required column 'normalization_method' in {input_file}. "
            "Ensure T013c (archard_normalization) has been run successfully."
        )
        
    # Count based on normalization_method flag
    # 'normalized' -> normalized_count
    # 'raw' -> raw_count
    normalized_count = int((df['normalization_method'] == 'normalized').sum())
    raw_count = int((df['normalization_method'] == 'raw').sum())
    total_count = len(df)
    
    counts = {
        "normalized_count": normalized_count,
        "raw_count": raw_count,
        "total_count": total_count
    }
    
    logger.info(f"Record counts calculated: {counts}")
    return counts

def save_record_counts(counts: Dict[str, int], output_path: Optional[Path] = None) -> None:
    """
    Save record counts to a JSON file.
    
    Args:
        counts: Dictionary containing the counts.
        output_path: Optional path for the output JSON. Defaults to RECORD_COUNTS_PATH.
    """
    if output_path is None:
        output_path = RECORD_COUNTS_PATH
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(counts, f, indent=2)
        
    logger.info(f"Record counts saved to: {output_path}")
    
    # Update hygiene hashes if hygiene module is active
    try:
        update_artifact_hash(output_path)
        save_artifact_hashes()
    except Exception as e:
        logger.warning(f"Could not update artifact hashes: {e}")

def compare_thresholds(counts: Dict[str, int]) -> Tuple[Dict[str, Any], int]:
    """
    Compare normalized_count against defined thresholds and determine study scope.
    
    Thresholds (SC-006, SC-004):
    - normalized_count < 100: status='failed', reason='insufficient_data', exit_code=1
    - 100 <= normalized_count < 300: study_scope='pilot_study', exit_code=2
    - normalized_count >= 300: study_scope='full_study', exit_code=0
    
    Args:
        counts: Dictionary containing 'normalized_count', 'raw_count', 'total_count'.
        
    Returns:
        Tuple of (result_dict, exit_code).
        result_dict contains: status, reason (if failed), study_scope, normalized_count.
    """
    normalized_count = counts.get('normalized_count', 0)
    
    if normalized_count < 100:
        result = {
            "status": "failed",
            "reason": "insufficient_data",
            "normalized_count": normalized_count
        }
        exit_code = 1
        logger.warning(f"Threshold check failed: normalized_count ({normalized_count}) < 100")
    elif 100 <= normalized_count < 300:
        result = {
            "status": "success",
            "study_scope": "pilot_study",
            "normalized_count": normalized_count
        }
        exit_code = 2
        logger.info(f"Threshold check passed (pilot): normalized_count ({normalized_count}) is in [100, 300)")
    else:
        result = {
            "status": "success",
            "study_scope": "full_study",
            "normalized_count": normalized_count
        }
        exit_code = 0
        logger.info(f"Threshold check passed (full): normalized_count ({normalized_count}) >= 300")
        
    return result, exit_code

def save_threshold_check(result: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """
    Save threshold check result to a JSON file.
    
    Args:
        result: Dictionary containing the threshold check result.
        output_path: Optional path for the output JSON. Defaults to THRESHOLD_CHECK_PATH.
    """
    if output_path is None:
        output_path = THRESHOLD_CHECK_PATH
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Threshold check saved to: {output_path}")
    
    try:
        update_artifact_hash(output_path)
        save_artifact_hashes()
    except Exception as e:
        logger.warning(f"Could not update artifact hashes: {e}")

def save_pre_check(result: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """
    Save pre-check result (specifically for failure cases) to reports/pre_check.json.
    
    Args:
        result: Dictionary containing the pre-check result.
        output_path: Optional path for the output JSON. Defaults to PRE_CHECK_PATH.
    """
    if output_path is None:
        output_path = PRE_CHECK_PATH
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Pre-check saved to: {output_path}")

def main():
    """
    Main entry point for T016b.
    1. Loads record counts from data/processed/record_counts.json.
    2. Compares normalized_count against thresholds.
    3. Writes data/processed/threshold_check.json.
    4. If failed (count < 100), writes reports/pre_check.json and exits with code 1.
    5. If pilot (100 <= count < 300), exits with code 2.
    6. If full study (count >= 300), exits with code 0.
    """
    setup_logging()
    logger.info("Starting T016b: compare_thresholds")
    
    try:
        # Ensure input file exists (T016a output)
        if not RECORD_COUNTS_PATH.exists():
            raise FileNotFoundError(
                f"Required input file missing: {RECORD_COUNTS_PATH}. "
                "Please ensure T016a (count_records) has completed successfully."
            )
        
        # Load record counts
        with open(RECORD_COUNTS_PATH, 'r') as f:
            counts = json.load(f)
        
        logger.info(f"Loaded record counts: {counts}")
        
        # Compare thresholds
        result, exit_code = compare_thresholds(counts)
        
        # Save threshold check result
        save_threshold_check(result)
        
        # If failed, write pre_check.json and exit
        if exit_code == 1:
            save_pre_check(result)
            logger.error(f"T016b failed: insufficient data. Exit code: {exit_code}")
            return exit_code
        
        # If pilot, exit with code 2
        if exit_code == 2:
            logger.warning(f"T016b completed as pilot study. Exit code: {exit_code}")
            return exit_code
        
        logger.info("T016b completed successfully (full study).")
        return 0
        
    except Exception as e:
        logger.error(f"T016b failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
