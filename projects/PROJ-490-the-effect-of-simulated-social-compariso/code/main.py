import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd

# Add the project root to path if running from different location
# Assuming this script is in code/main.py
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.download import load_or_generate_data
from data.preprocess import run_preprocess
from data.validate_raw import run_validation as run_raw_validation
from data.validate_imputed import run_validation as run_imputed_validation
from data.seed_generator import main as generate_seed
from analysis.regression import run_regression_analysis
from analysis.collinearity_handler import main as run_collinearity
from analysis.bootstrap import run_bootstrap_analysis
from analysis.sensitivity import main as run_sensitivity
from analysis.report_generator import run_report_generation
from utils.logger import configure_root_logger, log_execution_start, log_execution_end

def action_download():
    """Execute data discovery and loading."""
    log_execution_start("download")
    logger = logging.getLogger(__name__)
    try:
        # This triggers discovery, IRB check, synthetic fallback if needed, and saving to data/raw
        load_or_generate_data()
        # Generate seed file if synthetic path was taken (ensures artifact exists)
        generate_seed()
        # Validate raw data variables and schema
        run_raw_validation()
    except Exception as e:
        logger.error(f"Download action failed: {e}", exc_info=True)
        raise
    log_execution_end("download")

def action_preprocess():
    """Execute preprocessing and imputation."""
    log_execution_start("preprocess")
    logger = logging.getLogger(__name__)
    try:
        # Run preprocessing pipeline: load, check missingness, impute (MICE), save
        run_preprocess()
        # Validate imputed data (T013b)
        run_imputed_validation()
    except Exception as e:
        logger.error(f"Preprocess action failed: {e}", exc_info=True)
        raise
    log_execution_end("preprocess")

def action_analyze():
    """Execute statistical analysis."""
    log_execution_start("analyze")
    logger = logging.getLogger(__name__)
    try:
        # Run regression analysis (ANCOVA) - T018, T019, T021
        run_regression_analysis()
        # Run collinearity analysis (T022) - updates diagnostics
        run_collinearity()
        # Run bootstrap analysis (T025)
        run_bootstrap_analysis()
        # Run sensitivity analysis (T028a, T028b, T027, T029, T029a)
        run_sensitivity()
    except Exception as e:
        logger.error(f"Analyze action failed: {e}", exc_info=True)
        raise
    log_execution_end("analyze")

def action_validate():
    """Execute validation steps."""
    log_execution_start("validate")
    logger = logging.getLogger(__name__)
    try:
        # Re-run validations if needed or perform final checks
        run_raw_validation()
        run_imputed_validation()
    except Exception as e:
        logger.error(f"Validate action failed: {e}", exc_info=True)
        raise
    log_execution_end("validate")

def action_report():
    """Generate final report."""
    log_execution_start("report")
    logger = logging.getLogger(__name__)
    try:
        # Generates data/processed/final_report.json (T030, T030a)
        run_report_generation()
    except Exception as e:
        logger.error(f"Report action failed: {e}", exc_info=True)
        raise
    log_execution_end("report")

def main():
    parser = argparse.ArgumentParser(description="Main entry point for the pipeline.")
    parser.add_argument("--action", type=str, choices=["download", "preprocess", "analyze", "validate", "report", "all"],
                        help="Action to perform")
    args = parser.parse_args()

    configure_root_logger()
    logger = logging.getLogger(__name__)

    if args.action == "all":
        logger.info("Running full pipeline...")
        action_download()
        action_preprocess()
        action_analyze()
        action_report()
    elif args.action:
        if args.action == "download":
            action_download()
        elif args.action == "preprocess":
            action_preprocess()
        elif args.action == "analyze":
            action_analyze()
        elif args.action == "validate":
            action_validate()
        elif args.action == "report":
            action_report()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()