"""
Task T014b: Verify quality of the final retained dataset.

Calculates the mean Framewise Displacement (FD) of the final retained dataset
(after exclusion logic in T014a) and logs the value.

Verifies that mean FD <= 0.2 mm. If > 0.2 mm, logs a warning but continues.

This script assumes that preprocessing (T013) and exclusion (T014a) have been run
and that the preprocessed time series and associated metadata (including FD)
are stored in `data/processed/`.

Usage:
    python code/data/verify_quality.py
"""

import sys
import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.logging import get_logger, info, warning, error, debug
from code.config import ensure_directories, DATA_PROCESSED_PATH

logger = get_logger(__name__)

# Threshold for mean FD warning
MEAN_FD_THRESHOLD: float = 0.2

def load_preprocessing_metadata(processed_dir: Path) -> List[Dict[str, Any]]:
    """
    Load preprocessing metadata (including mean FD) from JSON files in the processed directory.
    
    Assumes that for each subject, there is a corresponding metadata file 
    (e.g., <subject_id>_metadata.json) containing the calculated mean FD.
    
    Args:
        processed_dir: Path to the data/processed directory.
        
    Returns:
        List of metadata dictionaries.
    """
    metadata_files = list(processed_dir.glob("*_metadata.json"))
    
    if not metadata_files:
        error(f"No preprocessing metadata files found in {processed_dir}")
        return []
    
    metadata_list = []
    for file_path in metadata_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Ensure mean_fd is present
                if 'mean_fd' not in data:
                    warning(f"Missing 'mean_fd' in {file_path.name}, skipping.")
                    continue
                metadata_list.append(data)
        except json.JSONDecodeError as e:
            error(f"Failed to parse JSON in {file_path}: {e}")
            continue
        except Exception as e:
            error(f"Unexpected error reading {file_path}: {e}")
            continue
    
    return metadata_list

def calculate_mean_fd(metadata_list: List[Dict[str, Any]]) -> float:
    """
    Calculate the mean FD across all subjects in the provided metadata list.
    
    Args:
        metadata_list: List of dictionaries containing 'mean_fd' keys.
        
    Returns:
        Mean FD value.
    """
    if not metadata_list:
        return 0.0
    
    fd_values = [item['mean_fd'] for item in metadata_list if 'mean_fd' in item]
    
    if not fd_values:
        return 0.0
        
    return float(np.mean(fd_values))

def verify_quality():
    """
    Main function to verify the quality of the final retained dataset.
    """
    info("Starting quality verification (Task T014b)...")
    
    # Ensure data directories exist
    ensure_directories()
    
    processed_dir = DATA_PROCESSED_PATH
    if not processed_dir.exists():
        error(f"Processed data directory does not exist: {processed_dir}")
        error("Please run preprocessing (T013) and exclusion (T014a) first.")
        return False
    
    # Load metadata
    metadata_list = load_preprocessing_metadata(processed_dir)
    
    if not metadata_list:
        error("No valid metadata found to verify quality.")
        return False
    
    info(f"Loaded metadata for {len(metadata_list)} subjects.")
    
    # Calculate mean FD
    overall_mean_fd = calculate_mean_fd(metadata_list)
    
    info(f"Mean FD of final retained dataset: {overall_mean_fd:.4f} mm")
    
    # Verify against threshold
    if overall_mean_fd > MEAN_FD_THRESHOLD:
        warning(f"Mean FD ({overall_mean_fd:.4f} mm) exceeds threshold ({MEAN_FD_THRESHOLD} mm).")
        warning("Proceeding with analysis, but data quality is suboptimal.")
        # Do not halt the pipeline as per task requirements
    else:
        info(f"Mean FD ({overall_mean_fd:.4f} mm) is within acceptable limits (<= {MEAN_FD_THRESHOLD} mm).")
    
    return True

def main():
    """Entry point for the script."""
    success = verify_quality()
    if not success:
        error("Quality verification failed or could not be completed.")
        sys.exit(1)
    info("Quality verification completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()