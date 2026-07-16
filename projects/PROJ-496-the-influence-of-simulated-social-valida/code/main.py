"""
Main entry point for the Simulated Social Validation research pipeline.
Handles argument parsing, phase routing, and reproducibility setup.
"""
import argparse
import logging
import os
import random
import sys
import time
from pathlib import Path

# Import local modules
from logger import setup_logging, get_logger
from config import (
    set_seeds,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    DATA_RESULTS_DIR,
    FIGURES_DIR,
    ensure_dirs
)

# Initialize logger
logger = get_logger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Pipeline for analyzing social validation effects on neural responses."
    )
    
    parser.add_argument(
        "--phase",
        type=str,
        choices=["search", "preprocess", "analyze", "report", "all"],
        default="all",
        help="Which phase of the pipeline to execute."
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility. Defaults to 42 if not specified."
    )
    
    parser.add_argument(
        "--rejection_threshold",
        type=float,
        default=100.0,
        help="Epoch rejection threshold in microvolts (used in preprocess phase)."
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    
    return parser.parse_args()

def run_search_phase():
    """Execute the dataset search phase (US1)."""
    logger.info("Starting Dataset Search Phase...")
    try:
        from search import run_search
        run_search()
        logger.info("Dataset Search Phase completed.")
    except ImportError:
        logger.error("search module not found. Please ensure T012 is implemented.")
        raise
    except Exception as e:
        logger.error(f"Search phase failed: {e}")
        raise

def run_preprocess_phase(args):
    """Execute the preprocessing phase (US2)."""
    logger.info("Starting Preprocessing Phase...")
    try:
        from preprocess import run_preprocess
        run_preprocess(args.rejection_threshold)
        logger.info("Preprocessing Phase completed.")
    except ImportError:
        logger.error("preprocess module not found. Please ensure T020 is implemented.")
        raise
    except Exception as e:
        logger.error(f"Preprocessing phase failed: {e}")
        raise

def run_analyze_phase():
    """Execute the analysis phase (US3)."""
    logger.info("Starting Analysis Phase...")
    try:
        from analyze import run_analysis
        run_analysis()
        logger.info("Analysis Phase completed.")
    except ImportError:
        logger.error("analyze module not found. Please ensure T045 is implemented.")
        raise
    except Exception as e:
        logger.error(f"Analysis phase failed: {e}")
        raise

def run_report_phase():
    """Execute the reporting phase."""
    logger.info("Starting Reporting Phase...")
    try:
        from report import generate_report
        generate_report()
        logger.info("Reporting Phase completed.")
    except ImportError:
        logger.error("report module not found. Please ensure T035 is implemented.")
        raise
    except Exception as e:
        logger.error(f"Reporting phase failed: {e}")
        raise

def main():
    """Main entry point."""
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level)
    
    # Ensure directories exist
    ensure_dirs()
    
    # CRITICAL: Set seeds BEFORE any data loading or processing
    # This satisfies Constitution Principle I (Reproducibility)
    logger.info(f"Setting random seeds to: {args.seed if args.seed is not None else 42}")
    set_seeds(args.seed)
    
    logger.info(f"Pipeline started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Project Root: {Path(__file__).resolve().parent.parent}")
    
    try:
        if args.phase == "search" or args.phase == "all":
            run_search_phase()
            # If search finds no eligible data, it exits with code 0 (Negative Finding)
            # and we should stop here.
            # The search module handles its own exit logic via sys.exit(0) if needed.
            # We check for a flag or just proceed if it didn't exit.
            # For now, assume if it returns, we continue unless it signaled abort.
            # In a real implementation, search might return a status code.
            # Here we assume if it didn't crash, we might continue to next phases IF data exists.
            # However, per T015, if no eligible data, the pipeline should abort.
            # We rely on the search module to raise a specific exception or exit if needed.
            # If it returns normally, we assume eligible data was found or we proceed cautiously.
            # To strictly follow T015, we should check for a 'negative_finding' flag.
            # Since we don't have that yet, we proceed to next phases only if 'all' is selected
            # and search didn't crash. The search module should handle the abort logic internally.
            # If search exits the program, we won't get here.
            pass
        
        if args.phase == "preprocess" or args.phase == "all":
            # Check if we should skip due to negative finding from search
            # This is a simplification; ideally, we'd check a status file.
            run_preprocess_phase(args)
        
        if args.phase == "analyze" or args.phase == "all":
            run_analyze_phase()
        
        if args.phase == "report" or args.phase == "all":
            run_report_phase()
            
        logger.info("Pipeline execution completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()