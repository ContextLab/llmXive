"""
Ground-Truth Validation Gate Script.

Executes the validation routine from T013 (validate_sample_statistics) on a fresh batch
of generated data to ensure data integrity before the Monte Carlo simulation begins.

This script MUST pass (exit code 0) before T018 can begin.
"""
import os
import sys
import logging
import argparse
from typing import List, Dict, Any, Tuple

from config import SimulationConfig, get_simulation_grid
from data_generator import generate_data, validate_sample_statistics

# Configure logging to write to a specific file for this task
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "ground_truth_validation.log")

def setup_logging():
    """Configure logging to write to the validation log file."""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Clear existing handlers to avoid duplicates if run multiple times in same session
    root_logger = logging.getLogger()
    root_logger.handlers = []
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_validation_batch(logger: logging.Logger) -> bool:
    """
    Run validation on a representative batch of configurations.
    
    Returns True if all validations pass, False otherwise.
    """
    logger.info("Starting Ground-Truth Validation Gate (T017b)...")
    logger.info("Generating fresh batch of data for validation...")
    
    # Define a representative batch of configurations to test
    # This covers different distributions, sample sizes, and effect sizes
    validation_configs = [
        {"sample_size": 30, "distribution": "normal", "effect_size": 0.0, "hypothesis": "null"},
        {"sample_size": 30, "distribution": "normal", "effect_size": 0.5, "hypothesis": "alt"},
        {"sample_size": 50, "distribution": "uniform", "effect_size": 0.0, "hypothesis": "null"},
        {"sample_size": 100, "distribution": "log_normal", "effect_size": 0.5, "hypothesis": "alt"},
        {"sample_size": 200, "distribution": "normal", "effect_size": 0.2, "hypothesis": "alt"},
    ]
    
    all_passed = True
    
    for i, config in enumerate(validation_configs):
        logger.info(f"Validating configuration {i+1}/{len(validation_configs)}: "
                    f"n={config['sample_size']}, dist={config['distribution']}, "
                    f"effect={config['effect_size']}, hyp={config['hypothesis']}")
        
        try:
            # Generate data
            data = generate_data(
                sample_size=config['sample_size'],
                distribution_type=config['distribution'],
                effect_size=config['effect_size'],
                hypothesis_type=config['hypothesis']
            )
            
            # Validate statistics
            is_valid, details = validate_sample_statistics(
                data,
                config['distribution'],
                config['effect_size'],
                config['hypothesis']
            )
            
            if is_valid:
                logger.info(f"  -> PASSED: {details}")
            else:
                logger.error(f"  -> FAILED: {details}")
                all_passed = False
                
        except Exception as e:
            logger.error(f"  -> ERROR: Exception during validation: {str(e)}")
            all_passed = False
    
    if all_passed:
        logger.info("Ground-Truth Validation Gate: ALL CHECKS PASSED.")
        logger.info("System ready for Monte Carlo simulation (T018).")
    else:
        logger.error("Ground-Truth Validation Gate: FAILED.")
        logger.error("Simulation (T018) must NOT proceed.")
        
    return all_passed

def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(description="Run Ground-Truth Validation Gate")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    logger = setup_logging()
    
    try:
        success = run_validation_batch(logger)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"Validation script failed with critical error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()