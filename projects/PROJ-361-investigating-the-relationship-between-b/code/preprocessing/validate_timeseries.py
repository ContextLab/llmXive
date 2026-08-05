"""
Validation script for extracted timeseries data.

Ensures that output matrices of dimensions T×N contain no NaN values.
This task (T016) is part of User Story 1 (Data Acquisition and Preprocessing).
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_processed_data_dir
from utils.logging_utils import get_logger, handle_pipeline_exception, PreprocessingError

logger = get_logger(__name__)


def validate_timeseries_matrix(matrix: np.ndarray, subject_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a timeseries matrix contains no NaN values.
    
    Args:
        matrix: 2D numpy array of shape (T, N) where T is time points and N is ROIs
        subject_id: Subject identifier for logging
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if no NaN values found, False otherwise
        - error_message: Description of validation failure if any
    """
    if matrix.ndim != 2:
        return False, f"Matrix for {subject_id} has {matrix.ndim} dimensions, expected 2 (T×N)"
    
    t, n = matrix.shape
    if t == 0 or n == 0:
        return False, f"Matrix for {subject_id} has invalid dimensions: {t}×{n}"
    
    nan_count = np.isnan(matrix).sum()
    if nan_count > 0:
        nan_ratio = nan_count / (t * n)
        return False, (
            f"Matrix for {subject_id} contains {nan_count} NaN values "
            f"({nan_ratio:.2%} of total elements)"
        )
    
    logger.info(f"Validation passed for {subject_id}: {t}×{n} matrix, no NaN values")
    return True, None


def validate_all_subjects(processed_dir: Optional[Path] = None) -> Dict[str, Dict]:
    """
    Validate all extracted timeseries files in the processed directory.
    
    Args:
        processed_dir: Path to processed data directory. If None, uses default config.
        
    Returns:
        Dictionary mapping subject_id to validation results
    """
    if processed_dir is None:
        processed_dir = get_processed_data_dir()
    
    results = {}
    total_subjects = 0
    valid_subjects = 0
    invalid_subjects = 0
    
    # Look for .npy files containing timeseries data
    timeseries_files = list(processed_dir.glob("timeseries_*.npy"))
    
    if not timeseries_files:
        logger.warning(f"No timeseries files found in {processed_dir}")
        return results
    
    for filepath in timeseries_files:
        subject_id = filepath.stem.replace("timeseries_", "")
        total_subjects += 1
        
        try:
            matrix = np.load(filepath)
            is_valid, error_msg = validate_timeseries_matrix(matrix, subject_id)
            
            results[subject_id] = {
                "valid": is_valid,
                "error": error_msg,
                "file": str(filepath),
                "shape": list(matrix.shape) if matrix.ndim == 2 else None
            }
            
            if is_valid:
                valid_subjects += 1
            else:
                invalid_subjects += 1
                logger.error(f"Validation FAILED for {subject_id}: {error_msg}")
                
        except Exception as e:
            results[subject_id] = {
                "valid": False,
                "error": f"Failed to load file: {str(e)}",
                "file": str(filepath),
                "shape": None
            }
            invalid_subjects += 1
            logger.error(f"Error processing {filepath}: {str(e)}")
    
    logger.info(
        f"Validation complete: {valid_subjects}/{total_subjects} subjects passed, "
        f"{invalid_subjects} failed"
    )
    
    return results


def main():
    """Main entry point for timeseries validation."""
    parser = argparse.ArgumentParser(
        description="Validate extracted timeseries data for NaN values"
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=None,
        help="Path to processed data directory (default: from config)"
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with error code if any validation fails"
    )
    
    args = parser.parse_args()
    
    try:
        results = validate_all_subjects(args.processed_dir)
        
        if not results:
            logger.warning("No subjects to validate")
            sys.exit(0)
        
        failed_count = sum(1 for r in results.values() if not r["valid"])
        
        if failed_count > 0 and args.fail_on_error:
            logger.error(f"{failed_count} subject(s) failed validation")
            sys.exit(1)
        
        sys.exit(0)
        
    except Exception as e:
        handle_pipeline_exception(e, "Timeseries validation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
