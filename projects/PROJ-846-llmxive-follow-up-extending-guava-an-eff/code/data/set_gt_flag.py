"""
T013d: GT Flag Set
Implements logic to set the global flag PERCEPTION_GT_AVAILABLE in config.py
based on the existence of the ground truth annotations file.
"""
import os
import sys
from pathlib import Path

# Add project root to path to ensure imports work when run as script
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.config import set_hyperparameter, get_path, initialize_paths
from utils.exceptions import DatasetUnavailableError

def check_ground_truth_availability(gt_path: Path) -> bool:
    """
    Checks if the ground truth annotations file exists at the specified path.
    
    Args:
        gt_path: Path to the expected ground truth annotations file.
        
    Returns:
        bool: True if file exists, False otherwise.
    """
    if not gt_path.exists():
        return False
    if not gt_path.is_file():
        return False
    return True

def set_gt_flag() -> bool:
    """
    Main logic for T013d.
    Checks for the existence of data/raw/guava/ground_truth_annotations.json.
    Updates the global configuration flag PERCEPTION_GT_AVAILABLE accordingly.
    
    Returns:
        bool: The value set for PERCEPTION_GT_AVAILABLE (True if available, False otherwise).
    """
    # Ensure paths are initialized
    initialize_paths()
    
    # Construct the expected path for ground truth annotations
    # Based on T013c output: data/raw/guava/ground_truth_annotations.json
    gt_file_path = get_path("raw_guava") / "ground_truth_annotations.json"
    
    is_available = check_ground_truth_availability(gt_file_path)
    
    # Update the global config flag
    # The config module uses a global dict to store hyperparameters/flags
    set_hyperparameter("PERCEPTION_GT_AVAILABLE", is_available)
    
    return is_available

def main():
    """
    Entry point for the script.
    Executes the GT flag check and prints the result.
    """
    try:
        is_available = set_gt_flag()
        status = "AVAILABLE" if is_available else "UNAVAILABLE"
        print(f"[T013d] Ground Truth Status: {status}")
        print(f"[T013d] Flag PERCEPTION_GT_AVAILABLE set to: {is_available}")
        
        if not is_available:
            # Log a warning but do not fail the script execution itself,
            # as the research pipeline is designed to handle missing GT
            # by setting gt_missing=true in later steps (T016).
            print("[T013d] WARNING: Ground truth annotations not found. "
                  "Downstream perception validation will skip GT comparison.")
        
        return 0
    except Exception as e:
        print(f"[T013d] ERROR: Failed to set GT flag: {e}")
        # Do not raise DatasetUnavailableError here; the flag logic is
        # designed to handle missing files gracefully by setting False.
        return 1

if __name__ == "__main__":
    sys.exit(main())
