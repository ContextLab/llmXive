import sys
import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in path for relative imports
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from utils.logging import get_logger, info, warning, error, debug

logger = get_logger(__name__)

def load_preprocessing_metadata(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Load preprocessing metadata JSON files from the data directory.
    Expects files like 'subject_001_metadata.json' in the provided directory.
    """
    metadata_list = []
    if not data_dir.exists():
        error(f"Data directory does not exist: {data_dir}")
        return metadata_list

    for file_path in data_dir.glob("*_metadata.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                metadata_list.append(data)
            debug(f"Loaded metadata from {file_path}")
        except (json.JSONDecodeError, IOError) as e:
            error(f"Failed to load metadata from {file_path}: {e}")
    
    return metadata_list

def calculate_mean_fd(metadata_list: List[Dict[str, Any]]) -> float:
    """
    Calculate the mean Framewise Displacement (FD) across all subjects.
    Expects each metadata dict to contain a 'mean_fd' key.
    """
    if not metadata_list:
        error("No metadata found to calculate mean FD.")
        return 0.0

    fd_values = []
    for meta in metadata_list:
        if 'mean_fd' in meta:
            fd_values.append(float(meta['mean_fd']))
        else:
            warning(f"Missing 'mean_fd' in metadata for subject: {meta.get('subject_id', 'unknown')}")

    if not fd_values:
        error("No valid FD values found in metadata.")
        return 0.0

    return float(np.mean(fd_values))

def verify_quality(data_dir: Path, threshold: float = 0.2) -> bool:
    """
    Verify the quality of the preprocessed dataset.
    1. Load metadata for all retained subjects.
    2. Calculate the mean FD of the final retained dataset.
    3. Log the value.
    4. Check if mean FD <= threshold.
       - If <= threshold: Log success.
       - If > threshold: Log a warning but return True (continue pipeline).
    """
    info(f"Starting quality verification for dataset in: {data_dir}")
    
    metadata_list = load_preprocessing_metadata(data_dir)
    
    if not metadata_list:
        error("Verification failed: No metadata found. Cannot calculate mean FD.")
        return False

    mean_fd = calculate_mean_fd(metadata_list)
    
    info(f"Final Retained Dataset Quality Check: Mean FD = {mean_fd:.4f} mm")
    
    if mean_fd <= threshold:
        info(f"Quality Check PASSED: Mean FD ({mean_fd:.4f} mm) is within threshold ({threshold} mm).")
        return True
    else:
        warning(f"Quality Check WARNING: Mean FD ({mean_fd:.4f} mm) exceeds threshold ({threshold} mm). "
                f"Proceeding with pipeline execution as per task requirements.")
        return True

def main():
    """
    Entry point for the verification script.
    Reads from data/processed/ by default.
    """
    data_dir = Path("data/processed")
    
    # Allow overriding via command line
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])

    success = verify_quality(data_dir, threshold=0.2)
    
    if success:
        info("Quality verification completed successfully.")
        sys.exit(0)
    else:
        error("Quality verification failed due to missing data.")
        sys.exit(1)

if __name__ == "__main__":
    main()