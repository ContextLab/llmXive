import argparse
import sys
import logging
import time
import os

# Import mode runners
from data_loader import run_data_load
from permutation import run_batch_permutation_test
from p_values_saver import run_p_values_saving
from power_analysis import run_power_analysis_mode
from corrected_p_values_saver import run_corrected_p_values_generation
from summary_generator import run_summary_generation
from visualization import run_visualization
from config import RESULTS_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="LLMXive Statistical Validity Pipeline")
    parser.add_argument('--mode', type=str, required=True, 
                      choices=['data_load', 'permutation', 'p_values', 'power_analysis', 'corrected_p_values', 'report', 'all'],
                      help='Execution mode')
    parser.add_argument('--queries', type=int, default=None, help='Number of queries to process (optional)')
    return parser.parse_args()

def run_data_load_mode():
    logger.info("Running data load mode...")
    run_data_load()

def run_permutation_mode():
    logger.info("Running permutation mode...")
    run_batch_permutation_test()

def run_p_values_mode():
    logger.info("Running raw p-values calculation mode...")
    run_p_values_saving()

def run_power_analysis_mode():
    logger.info("Running power analysis mode...")
    run_power_analysis_mode()

def run_corrected_p_values_mode():
    logger.info("Running corrected p-values generation mode (T026)...")
    run_corrected_p_values_generation()

def run_report_mode():
    logger.info("Running report generation mode...")
    run_summary_generation()
    run_visualization()

def run_all_modes():
    logger.info("Running all modes sequentially...")
    start = time.time()
    run_data_load_mode()
    run_permutation_mode()
    run_p_values_mode()
    run_power_analysis_mode()
    run_corrected_p_values_mode()
    run_report_mode()
    logger.info(f"Total runtime: {time.time() - start:.2f}s")

def main():
    args = parse_args()
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
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()