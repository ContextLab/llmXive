"""
Utility script to run validation on final_results.csv and ensure
exactly one row per valid subject.
"""
import os
import sys
import logging
from code.data.validation import run_validation_pipeline
from code.data.paths import get_processed_path
from code.config import set_seed

def main():
    """
    Main entry point for running validation on final_results.csv.
    
    This script ensures that the final_results.csv file contains exactly
    one row per valid subject, as required by T016.
    """
    set_seed(42)
    
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting validation pipeline for final_results.csv")
    
    # Run validation
    result = run_validation_pipeline()
    
    if result['valid']:
        logger.info(f"Validation PASSED: {result['subject_count']} unique subjects")
        return 0
    else:
        logger.error(f"Validation FAILED: {result['errors']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())