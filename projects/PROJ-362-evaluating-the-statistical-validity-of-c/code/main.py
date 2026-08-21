"""
Main entry point for the statistical validity evaluation pipeline.
Supports multiple modes: data_load, permutation, p_values, power_analysis, corrected_p_values, report.
"""
import argparse
import sys
import logging
import time
import os
from pathlib import Path
from config import ensure_dirs

# Import mode runners
from data_loader import run_data_load
from permutation import run_permutation_main
from p_values import run_p_value_calculation
from power_analysis import run_power_analysis_main
from corrected_p_values_saver import run_corrected_p_values_generation
from summary_generator import run_summary_generation
from visualization import run_visualization

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Statistical Validity Evaluation Pipeline")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["data_load", "permutation", "p_values", "power_analysis", "corrected_p_values", "report", "all"],
        default="all",
        help="Execution mode to run"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--permutations",
        type=int,
        default=1000,
        help="Number of permutations for null distribution"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance threshold for p-values"
    )
    return parser.parse_args()

def run_data_load_mode():
    logger.info("Running data load mode...")
    run_data_load()
    logger.info("Data load mode completed.")

def run_permutation_mode():
    logger.info("Running permutation mode...")
    run_permutation_main()
    logger.info("Permutation mode completed.")

def run_p_values_mode():
    logger.info("Running p-values calculation mode...")
    run_p_value_calculation()
    logger.info("P-values calculation mode completed.")

def run_power_analysis_mode():
    logger.info("Running power analysis mode...")
    run_power_analysis_main()
    logger.info("Power analysis mode completed.")

def run_corrected_p_values_mode():
    logger.info("Running corrected p-values generation mode...")
    run_corrected_p_values_generation()
    logger.info("Corrected p-values generation mode completed.")

def run_report_mode():
    logger.info("Running report generation mode...")
    run_summary_generation()
    run_visualization()
    logger.info("Report generation mode completed.")

def run_all_modes():
    logger.info("Running all modes sequentially...")
    ensure_dirs()
    run_data_load_mode()
    run_permutation_mode()
    run_p_values_mode()
    run_power_analysis_mode()
    run_corrected_p_values_mode()
    run_report_mode()
    logger.info("All modes completed.")

def main():
    args = parse_args()
    start_time = time.time()

    if args.mode == "data_load":
        run_data_load_mode()
    elif args.mode == "permutation":
        run_permutation_mode()
    elif args.mode == "p_values":
        run_p_values_mode()
    elif args.mode == "power_analysis":
        run_power_analysis_mode()
    elif args.mode == "corrected_p_values":
        run_corrected_p_values_mode()
    elif args.mode == "report":
        run_report_mode()
    elif args.mode == "all":
        run_all_modes()

    end_time = time.time()
    logger.info(f"Total execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()