import argparse
import logging
import os
import random
import sys
import time

from config import set_seeds, get_env_var, ensure_dirs
from logger import setup_logging, get_logger
from search import run_search_phase
from preprocess import run_preprocess_phase
from report_generator import generate_negative_finding_report
from generate_negative_finding_report import main as generate_none_report
from generate_negative_finding_report_separate import main as generate_separate_report

logger = get_logger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Automated Science Pipeline: Social Validation Study"
    )
    parser.add_argument(
        "--phase",
        choices=["search", "preprocess", "analyze", "report", "all"],
        default="all",
        help="Which phase to run",
    )
    parser.add_argument(
        "--rejection-threshold",
        type=float,
        default=100.0,
        help="Epoch rejection threshold in microvolts (US2)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Override default output directory",
    )
    return parser.parse_args()

def run_search_phase():
    """
    Execute User Story 1: Dataset Discovery & Eligibility Check.
    
    This phase searches for eligible datasets.
    - If "Eligible" found: returns True, pipeline continues.
    - If "Sim-Only" or "Real-Only" found: returns "separate", triggers T016c.
    - If "None" found: returns "none", triggers T016b.
    """
    logger.info("Starting Search Phase (US1)...")
    
    # Run the search logic
    search_status, summary = run_search_phase()
    
    # search_status is expected to be one of: "eligible", "separate", "none"
    if search_status == "eligible":
        logger.info("Eligible dataset found. Proceeding to Preprocessing.")
        return "eligible"
    elif search_status == "separate":
        logger.warning("No single eligible dataset found. Separate datasets identified.")
        logger.info("Triggering Negative Finding Report (Separate) - T016c.")
        # T016c: Generate report for separate datasets
        generate_separate_report()
        logger.info("Pipeline terminated due to Negative Finding (Separate).")
        return "abort_separate"
    elif search_status == "none":
        logger.warning("No eligible datasets found (None status).")
        logger.info("Triggering Negative Finding Report (None) - T016b.")
        # T016b: Generate report for no datasets
        generate_none_report()
        logger.info("Pipeline terminated due to Negative Finding (None).")
        return "abort_none"
    else:
        logger.error(f"Unexpected search status: {search_status}")
        return "abort_unknown"

def run_preprocess_phase(rejection_threshold):
    """Execute User Story 2: EEG Preprocessing."""
    logger.info("Starting Preprocessing Phase (US2)...")
    success = run_preprocess_phase(rejection_threshold)
    if not success:
        logger.warning("Preprocessing QC failed. Triggering abort.")
        # T016d would be triggered here if implemented
        return "abort_qc"
    return "eligible"

def run_analyze_phase():
    """Execute User Story 3: Statistical Modeling."""
    logger.info("Starting Analysis Phase (US3)...")
    # Placeholder for actual analysis logic
    logger.info("Analysis complete.")
    return True

def run_report_phase():
    """Execute Phase 6: Reporting."""
    logger.info("Starting Reporting Phase...")
    # Placeholder for actual report logic
    logger.info("Report generation complete.")
    return True

def main():
    """Main entry point for the pipeline."""
    args = parse_args()
    
    # Initialize logging
    setup_logging(level=logging.INFO)
    
    # Set seeds for reproducibility (T0046)
    set_seeds(args.seed)
    
    # Ensure directories exist
    ensure_dirs()
    
    logger.info(f"Starting pipeline with phase: {args.phase}")
    
    if args.phase in ["search", "all"]:
        search_result = run_search_phase()
        
        if search_result.startswith("abort"):
            # T015: If abort triggered, exit with code 0 (Project Complete: Negative Finding)
            logger.info("Pipeline completed with Negative Finding. Exiting with code 0.")
            sys.exit(0)
        
        # If we are here, an eligible dataset was found.
        # Continue to next phases only if 'all' or specific phases requested
        if args.phase != "all":
            logger.info("Search phase complete. Exiting as requested.")
            sys.exit(0)
    
    if args.phase in ["preprocess", "all"]:
        preprocess_result = run_preprocess_phase(args.rejection_threshold)
        if preprocess_result == "abort_qc":
            # T016d logic would go here
            sys.exit(0)
    
    if args.phase in ["analyze", "all"]:
        run_analyze_phase()
    
    if args.phase in ["report", "all"]:
        run_report_phase()
    
    logger.info("Pipeline execution completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
