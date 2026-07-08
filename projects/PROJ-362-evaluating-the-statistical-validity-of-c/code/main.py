import argparse
import sys
import logging
import time
import os
from code.config import LOG_LEVEL, RESULTS_DIR, DATA_RAW_DIR, ensure_dirs
from code.data_loader import run_data_load
from code.permutation import run_batch_permutation_test
from code.p_values import run_p_value_calculation
from code.power_analysis import run_power_analysis, run_bh_correction
from code.sensitivity_analysis import run_sensitivity_analysis
from code.corrected_p_values_saver import run_corrected_p_values_generation
from code.mdes_summary_generator import run_mdes_summary_generation
from code.visualization import generate_plots

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Statistical Validity of Ranking Metrics Pipeline")
    parser.add_argument('--mode', type=str, required=True,
                        choices=['data_load', 'permutation', 'p_values', 'power_analysis',
                                 'mdes_summary', 'sensitivity', 'corrected_p_values', 'report', 'all'],
                        help="Execution mode")
    parser.add_argument('--query_limit', type=int, default=None,
                        help="Limit number of queries to process (for testing)")
    return parser.parse_args()

def run_data_load_mode(args):
    logger.info("Starting data load mode...")
    run_data_load(query_limit=args.query_limit)
    logger.info("Data load mode completed.")

def run_permutation_mode(args):
    logger.info("Starting permutation mode...")
    run_batch_permutation_test(query_limit=args.query_limit)
    logger.info("Permutation mode completed.")

def run_p_values_mode(args):
    logger.info("Starting p-values calculation mode...")
    run_p_value_calculation()
    logger.info("P-values calculation mode completed.")

def run_power_analysis_mode(args):
    logger.info("Starting power analysis mode...")
    run_power_analysis()
    logger.info("Power analysis mode completed.")

def run_mdes_summary_mode(args):
    logger.info("Starting MDES summary generation mode...")
    run_mdes_summary_generation()
    logger.info("MDES summary generation mode completed.")

def run_sensitivity_mode(args):
    logger.info("Starting sensitivity analysis mode...")
    run_sensitivity_analysis()
    logger.info("Sensitivity analysis mode completed.")

def run_corrected_p_values_mode(args):
    logger.info("Starting corrected p-values generation mode...")
    run_corrected_p_values_generation()
    logger.info("Corrected p-values generation mode completed.")

def run_report_mode(args):
    logger.info("Starting report generation mode...")
    generate_plots()
    logger.info("Report generation mode completed.")

def run_all_modes(args):
    logger.info("Starting all modes...")
    start_time = time.time()
    
    run_data_load_mode(args)
    run_permutation_mode(args)
    run_p_values_mode(args)
    run_power_analysis_mode(args)
    run_mdes_summary_mode(args)
    run_sensitivity_mode(args)
    run_corrected_p_values_mode(args)
    run_report_mode(args)
    
    elapsed = time.time() - start_time
    logger.info(f"All modes completed in {elapsed:.2f} seconds.")
    
    # FR-008: Explicit text generation for findings
    logger.info("Findings indicate statistical association, not causal algorithmic improvement")

def main():
    args = parse_args()
    ensure_dirs()

    if args.mode == 'data_load':
        run_data_load_mode(args)
    elif args.mode == 'permutation':
        run_permutation_mode(args)
    elif args.mode == 'p_values':
        run_p_values_mode(args)
    elif args.mode == 'power_analysis':
        run_power_analysis_mode(args)
    elif args.mode == 'mdes_summary':
        run_mdes_summary_mode(args)
    elif args.mode == 'sensitivity':
        run_sensitivity_mode(args)
    elif args.mode == 'corrected_p_values':
        run_corrected_p_values_mode(args)
    elif args.mode == 'report':
        run_report_mode(args)
    elif args.mode == 'all':
        run_all_modes(args)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)

if __name__ == '__main__':
    main()