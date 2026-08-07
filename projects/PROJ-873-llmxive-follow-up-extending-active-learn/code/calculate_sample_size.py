"""
calculate_sample_size.py - Calculate sample size for LLM consensus validation.

This module implements T013b:
- Calculate sample size as max(10, 5% of flagged count)
- Write sample_config.json
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

from config import get_config

logger = logging.getLogger(__name__)

def calculate_dynamic_sample_size(flagged_count: int, percentage: float = 0.05, minimum: int = 10):
    """
    Calculate the dynamic sample size for consensus validation.
    
    Args:
        flagged_count: Total number of flagged (wasted) pairs
        percentage: Percentage of flagged pairs to sample (default 5%)
        minimum: Minimum sample size (default 10)
        
    Returns:
        Calculated sample size
    """
    calculated = int(flagged_count * percentage)
    return max(minimum, calculated)

def main():
    """Entry point for sample size calculation."""
    parser = argparse.ArgumentParser(description="Calculate sample size for consensus validation")
    parser.add_argument("--flagged-file", type=str, default=None,
                      help="Path to flagged_pairs_count.json")
    parser.add_argument("--output", type=str, default=None,
                      help="Path to output sample_config.json")
    
    args = parser.parse_args()
    
    config = get_config()
    
    # Default paths
    flagged_file = args.flagged_file or Path(config.data_dir) / "results" / "flagged_pairs_count.json"
    output_file = args.output or Path(config.data_dir) / "results" / "sample_config.json"
    
    # Ensure results directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Load flagged count
    if not Path(flagged_file).exists():
        raise FileNotFoundError(f"Flagged pairs count not found: {flagged_file}")
    
    with open(flagged_file, 'r') as f:
        flagged_data = json.load(f)
    
    flagged_count = flagged_data.get("wasted_count", 0)
    logger.info(f"Total flagged pairs: {flagged_count}")
    
    # Calculate sample size
    sample_size = calculate_dynamic_sample_size(flagged_count)
    logger.info(f"Calculated sample size: {sample_size}")
    
    # Write sample config
    sample_config = {
        "sample_size": sample_size,
        "minimum_threshold": 10,
        "percentage": 0.05
    }
    
    with open(output_file, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    logger.info(f"Sample config written to {output_file}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
