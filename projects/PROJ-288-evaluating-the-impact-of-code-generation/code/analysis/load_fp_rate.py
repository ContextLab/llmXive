"""
Load baseline corpus false positive rate for SIMEX correction.

This module implements task T026a: Load the false positive rate estimated
from the baseline corpus (output of T018) to determine if SIMEX correction
is required for misclassification bias.

Input: data/baseline_corpus/estimated_fp_rate.json
Output: Returns the fp_rate value or raises an error if not found.
"""
import json
import sys
from pathlib import Path
from typing import Optional

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from data.logging_config import get_logger

logger = get_logger(__name__)

def load_fp_rate(file_path: str = "data/baseline_corpus/estimated_fp_rate.json") -> float:
    """
    Load the false positive rate from the baseline corpus estimation file.
    
    Args:
        file_path: Path to the JSON file containing the false positive rate.
                   Defaults to the standard output location of T018.
    
    Returns:
        float: The false positive rate (fp_rate) value.
    
    Raises:
        FileNotFoundError: If the specified file does not exist.
        KeyError: If the 'fp_rate' key is missing from the JSON.
        json.JSONDecodeError: If the file contains invalid JSON.
        ValueError: If the fp_rate is not a valid number.
    """
    path = Path(file_path)
    
    if not path.exists():
        logger.error(f"False positive rate file not found: {path}")
        raise FileNotFoundError(f"Baseline corpus FP rate file not found: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        raise
    
    if 'fp_rate' not in data:
        logger.error(f"'fp_rate' key missing in {path}. Available keys: {list(data.keys())}")
        raise KeyError("'fp_rate' key not found in the JSON file.")
    
    fp_rate = data['fp_rate']
    
    if not isinstance(fp_rate, (int, float)):
        logger.error(f"fp_rate is not a number: {type(fp_rate)}")
        raise ValueError(f"fp_rate must be a number, got {type(fp_rate)}")
    
    if fp_rate < 0 or fp_rate > 1:
        logger.warning(f"fp_rate {fp_rate} is outside expected range [0, 1].")
    
    logger.info(f"Loaded false positive rate: {fp_rate}")
    return float(fp_rate)

def main():
    """
    Main entry point to load and display the false positive rate.
    This script is intended to be run to verify the data exists and is readable.
    """
    try:
        fp_rate = load_fp_rate()
        print(f"Successfully loaded false positive rate: {fp_rate}")
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as e:
        print(f"Failed to load false positive rate: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())