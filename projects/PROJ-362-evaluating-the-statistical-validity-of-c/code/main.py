"""
Main entry point for the statistical validity evaluation pipeline.
"""

import argparse
import sys
import logging
import time
import os
from pathlib import Path

from data_loader import run_data_load
from permutation import run_batch_permutation_test
from p_values import run_p_value_calculation
from p_values_saver import run_p_values_saving
from config import ensure_dirs, RESULTS_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Statistical Validity Evaluation Pipeline")
    parser.add_argument('--mode', type=str, required=True, 
                        choices=['data_load', 'permutation', 'p_values', 'power_analysis', 'corrected_p_values', 'report', 'all'],
                        help='Mode to run')
    parser.add_argument('--queries', type=int, default=None,
                        help='Number of queries to process (for subsampling).')
    return parser.parse_args()

def run_data_load_mode():
    logger.info("Running Data Load mode...")
    run_data_load()
    logger.info("Data Load complete.")

def run_permutation_mode():
    logger.info("Running Permutation mode...")
    # This would typically load data and call run_batch_permutation_test
    # For now, we assume data is loaded and we just demonstrate the call structure
    # In a real run, we'd load the qrels here
    logger.warning("Permutation mode requires loaded data. Please run data_load mode first.")
    # Placeholder for actual implementation logic that loads data and runs permutation
    # This is where T014 (batch processing) and T015 (runtime monitor) would integrate
    logger.info("Permutation mode finished (placeholder).")

def run_p_values_mode():
    logger.info("Running P-Values mode...")
    # Placeholder: Assumes permutation results exist
    logger.warning("P-Values mode requires permutation results.")
    logger.info("P-Values mode finished (placeholder).")

def run_power_analysis_mode():
    logger.info("Running Power Analysis mode...")
    logger.warning("Power Analysis mode not yet implemented.")
    logger.info("Power Analysis mode finished (placeholder).")

def run_corrected_p_values_mode():
    logger.info("Running Corrected P-Values mode...")
    logger.warning("Corrected P-Values mode not yet implemented.")
    logger.info("Corrected P-Values mode finished (placeholder).")

def run_report_mode():
    logger.info("Running Report mode...")
    logger.warning("Report mode not yet implemented.")
    logger.info("Report mode finished (placeholder).")

def run_all_modes():
    logger.info("Running all modes...")
    run_data_load_mode()
    run_permutation_mode()
    run_p_values_mode()
    run_power_analysis_mode()
    run_corrected_p_values_mode()
    run_report_mode()
    logger.info("All modes complete.")

def main():
    args = parse_args()
    ensure_dirs()
    
    start_time = time.time()
    
    if args.mode == 'data_load':
        run_data_load_mode()
    elif args.mode == 'permutation':
        run_permutation_mode()
    elif args.mode == 'p_values':
        run_p_values_mode()
    elif args.mode == 'power_analysis':
        run_power_analysis_mode()
    elif args.mode == 'corrected_p_values':
        run_corrected_p_values_mode()
    elif args.mode == 'report':
        run_report_mode()
    elif args.mode == 'all':
        run_all_modes()
    
    elapsed = time.time() - start_time
    logger.info(f"Total execution time: {elapsed:.2f} seconds")

if __name__ == '__main__':
    main()