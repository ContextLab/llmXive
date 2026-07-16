import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from data_models import PolymerRecord
from utils import get_logger

# Configuration
MIN_DATASET_SIZE = 150
WARNING_FILE_PATH = "data/reports/power_analysis_warning.txt"

def check_dataset_power(dataset_size: int, min_size: int = MIN_DATASET_SIZE) -> bool:
    """
    Check if the dataset size meets the minimum power requirement.
    
    Args:
        dataset_size: The number of records in the dataset.
        min_size: The minimum required dataset size (default 150).
        
    Returns:
        True if the dataset size is sufficient, False otherwise.
    """
    return dataset_size >= min_size

def run_power_analysis_from_csv(
    records: List[PolymerRecord],
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Perform power analysis on the provided dataset records.
    
    Calculates the dataset size, checks against the minimum threshold,
    and generates a warning report if the dataset is too small.
    
    Args:
        records: List of PolymerRecord objects to analyze.
        logger: Optional logger instance. If None, a default logger is used.
        
    Returns:
        A dictionary containing:
            - 'dataset_size': int
            - 'is_powered': bool
            - 'warning_generated': bool
            - 'warning_path': str or None
    """
    if logger is None:
        logger = get_logger(__name__)
    
    dataset_size = len(records)
    is_powered = check_dataset_power(dataset_size)
    
    result = {
        "dataset_size": dataset_size,
        "is_powered": is_powered,
        "warning_generated": False,
        "warning_path": None
    }
    
    if not is_powered:
        warning_msg = (
            f"POWER ANALYSIS WARNING: Dataset size ({dataset_size}) is below "
            f"the minimum threshold ({MIN_DATASET_SIZE}). "
            "Statistical power for the study may be insufficient. "
            "Consider collecting more data or adjusting the experimental design."
        )
        
        logger.warning(warning_msg)
        
        # Ensure the reports directory exists
        reports_dir = Path(WARNING_FILE_PATH).parent
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Write the warning file
        with open(WARNING_FILE_PATH, 'w') as f:
            f.write(warning_msg)
            f.write("\n")
            f.write(f"Timestamp: {os.popen('date').read().strip()}\n")
            f.write(f"Dataset Size: {dataset_size}\n")
            f.write(f"Minimum Required: {MIN_DATASET_SIZE}\n")
        
        result["warning_generated"] = True
        result["warning_path"] = str(Path(WARNING_FILE_PATH).resolve())
        
        logger.info(f"Power analysis warning written to: {result['warning_path']}")
    
    return result
