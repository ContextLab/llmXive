"""
Script to execute Task T013b: Sample Size Calculation for LLM Consensus Validation.

This script reads the flagged pairs count from data/results/flagged_pairs_count.json,
calculates the appropriate sample size, and writes the configuration to 
data/results/sample_config.json.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from metrics import run_sample_size_calculation

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    flagged_count_file = project_root / "data" / "results" / "flagged_pairs_count.json"
    output_file = project_root / "data" / "results" / "sample_config.json"
    
    logger.info(f"Executing T013b: Sample size calculation")
    logger.info(f"Input file: {flagged_count_file}")
    logger.info(f"Output file: {output_file}")
    
    if not flagged_count_file.exists():
        logger.error(f"Input file not found: {flagged_count_file}")
        logger.error("T013b requires T013 to be completed first (flagged_pairs_count.json)")
        sys.exit(1)
    
    try:
        result = run_sample_size_calculation(str(flagged_count_file), str(output_file))
        logger.info(f"T013b completed successfully. Sample size: {result['sample_size']}")
        logger.info(f"Skip validation: {result['skip_validation']}")
    except Exception as e:
        logger.error(f"T013b failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
