"""
Execution script for T058b: Execute Edge Case Sensitivity Analysis.

This script runs the flat object sensitivity sweep implemented in T058a
(code/stats/sensitivity.py) and writes the results to 
results/analysis/flat_object_sensitivity.csv.

It loads the final paired dataset, identifies flat objects, runs the
sensitivity analysis over a range of epsilon values, and writes the CSV.
"""
import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any, Optional

# Add project root to path if running as script
if 'code' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from stats.sensitivity import run_flat_object_sensitivity_analysis, write_flat_object_sensitivity_csv, load_comparison_results_for_flat_analysis
from utils.logging import setup_logging

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Execute Flat Object Sensitivity Analysis (T058b)')
    parser.add_argument('--input-csv', type=str, 
                        default='results/analysis/final_paired_dataset.csv',
                        help='Path to the final paired dataset CSV')
    parser.add_argument('--output-csv', type=str,
                        default='results/analysis/flat_object_sensitivity.csv',
                        help='Path to write the sensitivity analysis CSV')
    parser.add_argument('--config', type=str,
                        default='data/power_config.yaml',
                        help='Path to power config (for epsilon range if needed)')
    return parser.parse_args()

def main():
    args = parse_args()
    setup_logging()
    
    logger.info(f"Starting Flat Object Sensitivity Analysis (T058b)")
    logger.info(f"Input: {args.input_csv}")
    logger.info(f"Output: {args.output_csv}")

    if not os.path.exists(args.input_csv):
        logger.error(f"Input file not found: {args.input_csv}")
        logger.error("T058b requires T047c (Final Paired Dataset) to have been executed.")
        sys.exit(1)

    if not os.path.exists(args.config):
        logger.warning(f"Config file not found: {args.config}. Using default epsilon range.")

    # 1. Load the final paired dataset
    logger.info("Loading final paired dataset...")
    try:
        paired_data = load_comparison_results_for_flat_analysis(args.input_csv)
    except Exception as e:
        logger.error(f"Failed to load paired dataset: {e}")
        sys.exit(1)

    if not paired_data:
        logger.error("Paired dataset is empty. Cannot run sensitivity analysis.")
        sys.exit(1)

    # 2. Run the sensitivity analysis
    # The sensitivity.py module handles the logic of identifying flat objects
    # and sweeping over epsilon values.
    logger.info("Running flat object sensitivity analysis...")
    try:
        sensitivity_results = run_flat_object_sensitivity_analysis(paired_data)
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    if not sensitivity_results:
        logger.warning("Sensitivity analysis produced no results. Check if flat objects exist in dataset.")
        # Create an empty file with headers to indicate the run happened but found no data
        write_flat_object_sensitivity_csv([], args.output_csv)
        return

    # 3. Write the results to CSV
    logger.info(f"Writing results to {args.output_csv}...")
    try:
        write_flat_object_sensitivity_csv(sensitivity_results, args.output_csv)
    except Exception as e:
        logger.error(f"Failed to write sensitivity CSV: {e}")
        sys.exit(1)

    logger.info(f"Flat Object Sensitivity Analysis completed successfully.")
    logger.info(f"Output written to: {args.output_csv}")

if __name__ == '__main__':
    main()
