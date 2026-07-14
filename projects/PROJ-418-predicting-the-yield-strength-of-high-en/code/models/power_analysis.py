"""
Power analysis and edge case handling for statistical validation.

Handles the edge case where sample size N < 50, ensuring
output/power_analysis.json is written with the appropriate status
and logging a WARNING message.
"""
import os
import json
import logging
from typing import Dict, Any, Optional

from utils.logging import get_logger

logger = get_logger(__name__)

OUTPUT_DIR = "output"
POWER_ANALYSIS_FILE = os.path.join(OUTPUT_DIR, "power_analysis.json")
MIN_POWER_THRESHOLD = 50


def check_sample_size_power(n_samples: int) -> Dict[str, Any]:
    """
    Check if sample size meets minimum power requirements.
    
    Args:
        n_samples: The number of samples in the dataset.
        
    Returns:
        A dictionary with 'status' and 'n_samples' keys.
        If n_samples < 50, status is 'insufficient_power'.
        Otherwise, status is 'sufficient_power'.
    """
    if n_samples < MIN_POWER_THRESHOLD:
        status = "insufficient_power"
        logger.warning(f"INSUFFICIENT_POWER: N={n_samples} < {MIN_POWER_THRESHOLD}")
    else:
        status = "sufficient_power"
        logger.info(f"Power check passed: N={n_samples} >= {MIN_POWER_THRESHOLD}")
    
    return {
        "status": status,
        "n_samples": n_samples,
        "threshold": MIN_POWER_THRESHOLD
    }


def write_power_analysis(n_samples: int, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Write power analysis results to output/power_analysis.json.
    
    This function handles the edge case where N < 50 by writing
    a status of 'insufficient_power' and logging a WARNING message.
    
    Args:
        n_samples: The number of samples in the dataset.
        output_path: Optional path to write the JSON file. Defaults to output/power_analysis.json.
        
    Returns:
        The power analysis dictionary that was written.
    """
    if output_path is None:
        output_path = POWER_ANALYSIS_FILE
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Check power status (this also logs the warning if needed)
    power_result = check_sample_size_power(n_samples)
    
    # Write to JSON file
    with open(output_path, 'w') as f:
        json.dump(power_result, f, indent=2)
    
    logger.info(f"Power analysis written to {output_path}")
    return power_result


def main():
    """
    Main entry point for power analysis script.
    
    This script is intended to be called from the evaluation pipeline
    after data loading but before expensive statistical tests.
    It checks sample size and writes the power analysis result.
    """
    # This function can be called with a specific N or derived from a dataset
    # For now, we'll demonstrate with a placeholder - in real usage,
    # this would be called with actual data count from the pipeline
    import sys
    
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
            result = write_power_analysis(n)
            print(f"Power analysis result: {result}")
        except ValueError:
            logger.error(f"Invalid sample size: {sys.argv[1]}")
            sys.exit(1)
    else:
        # Default demonstration - in real pipeline this is called with actual N
        logger.info("No sample size provided. Use: python code/models/power_analysis.py <n_samples>")
        sys.exit(0)


if __name__ == "__main__":
    main()