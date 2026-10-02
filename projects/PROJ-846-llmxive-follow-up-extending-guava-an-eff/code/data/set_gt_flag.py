import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Import project utilities
from utils.config import set_hyperparameter, get_path, initialize_paths
from utils.errors import DatasetUnavailableError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_ground_truth_availability() -> bool:
    """
    Check if the ground truth annotations file exists and is valid.
    
    Returns:
        bool: True if ground truth is available, False otherwise.
    """
    try:
        gt_path = get_path("ground_truth_annotations")
        if not gt_path or not gt_path.exists():
            logger.warning(f"Ground truth file not found at: {gt_path}")
            return False
        
        # Basic validation: try to load as JSON
        with open(gt_path, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict) and not isinstance(data, list):
                logger.warning(f"Ground truth file is not a valid JSON structure: {gt_path}")
                return False
            
        logger.info(f"Ground truth file validated successfully: {gt_path}")
        return True
    except Exception as e:
        logger.error(f"Error validating ground truth file: {e}")
        return False

def set_gt_flag(is_available: bool) -> None:
    """
    Set the DATASET_AVAILABLE flag in the project configuration.
    
    Args:
        is_available (bool): Whether the dataset/ground truth is available.
    """
    try:
        # Initialize paths to ensure config is ready
        initialize_paths()
        
        # Set the hyperparameter
        set_hyperparameter("DATASET_AVAILABLE", str(is_available).lower())
        
        status = "AVAILABLE" if is_available else "UNAVAILABLE"
        logger.info(f"Dataset availability flag set to: {status}")
        
        # Also write a status file for easy downstream checking
        status_file = get_path("dataset_status")
        if status_file:
            status_data = {
                "dataset_available": is_available,
                "checked_at": str(Path().resolve()),
                "reason": "Ground truth validation" if is_available else "Ground truth missing or invalid"
            }
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
            logger.info(f"Dataset status written to: {status_file}")
            
    except Exception as e:
        logger.error(f"Failed to set dataset availability flag: {e}")
        raise

def main():
    """
    Main entry point for checking ground truth availability and setting the flag.
    
    This task (T013c) handles missing dataset gracefully:
    1. Checks if ground truth annotations exist
    2. Logs the condition
    3. Sets DATASET_AVAILABLE flag accordingly
    4. Allows downstream tasks to skip or use mock data based on the flag
    """
    logger.info("Starting ground truth availability check (Task T013c)...")
    
    try:
        # Initialize paths
        initialize_paths()
        
        # Check availability
        is_available = check_ground_truth_availability()
        
        # Set the flag gracefully - never raise DatasetUnavailableError here
        # This task is specifically for graceful handling
        set_gt_flag(is_available)
        
        if not is_available:
            logger.warning("Dataset is NOT available. Downstream tasks should handle this gracefully.")
            logger.warning("Consider using mock data or skipping processing for this run.")
        else:
            logger.info("Dataset is available. Proceeding with normal processing.")
            
        return 0 if is_available else 1  # Return 1 if unavailable, but don't crash
        
    except Exception as e:
        logger.error(f"Unexpected error during dataset availability check: {e}")
        # Even on unexpected error, try to set flag to false gracefully
        try:
            set_gt_flag(False)
        except:
            pass
        return 2

if __name__ == "__main__":
    sys.exit(main())