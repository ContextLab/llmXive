"""
Main orchestration script for the Climate-Smart Agriculture Optimization Pipeline.

This script coordinates data ingestion, processing, analysis, and reporting.
It handles real data checks and triggers synthetic data generation in CI environments
when real data is missing, adhering to strict fail-loudly principles.
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Import from existing project modules
from src.utils.io_helpers import FatalError, setup_logging
from src.data.generators.synthetic_generator import main as generate_synthetic_main

# Configure logging
logger = logging.getLogger(__name__)

def check_and_generate_synthetic_data(dry_run: bool = False) -> bool:
    """
    Check for real data in data/raw/. If missing AND CI=true, invoke synthetic generator.
    
    Args:
        dry_run: If True, only log actions without executing them.
        
    Returns:
        True if real data exists or synthetic data was generated successfully.
        False if no data is available and synthetic generation was not triggered.
    """
    raw_data_dir = Path("data/raw")
    ci_mode = os.environ.get("CI", "").lower() == "true"
    
    # Check if real data exists
    if raw_data_dir.exists() and any(raw_data_dir.iterdir()):
        logger.info("Real data detected in data/raw/. Proceeding with pipeline.")
        return True
    
    logger.warning("No real data found in data/raw/.")
    
    if ci_mode:
        logger.info("CI environment detected. Triggering synthetic data generation.")
        if dry_run:
            logger.info("[DRY-RUN] Would invoke synthetic generator now.")
            return True
        
        try:
            # Invoke the synthetic generator main function
            # This will generate data to data/processed/analysis_dataset.csv
            generate_synthetic_main()
            logger.info("Synthetic data generation completed successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to generate synthetic data: {e}")
            raise FatalError("Synthetic data generation failed in CI mode.") from e
    else:
        logger.warning("Not in CI mode. Cannot generate synthetic data automatically.")
        return False

def run_pipeline(args: argparse.Namespace) -> int:
    """
    Execute the main pipeline logic.
    
    Args:
        args: Parsed command line arguments.
        
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    if args.dry_run:
        logger.info("Running in DRY-RUN mode. No actual data processing will occur.")
        # In dry-run, we just verify the logic flow
        if args.no_synthetic:
            logger.warning("[DRY-RUN] --no-synthetic flag provided. Would raise FatalError if data missing.")
            raw_data_dir = Path("data/raw")
            if not (raw_data_dir.exists() and any(raw_data_dir.iterdir())):
                logger.error("No real data found. With --no-synthetic, this would be fatal.")
                return 1
        else:
            check_and_generate_synthetic_data(dry_run=True)
        return 0

    # Check for synthetic data requirements
    if args.no_synthetic:
        raw_data_dir = Path("data/raw")
        if not (raw_data_dir.exists() and any(raw_data_dir.iterdir())):
            raise FatalError("No real data found and --no-synthetic flag was provided. Aborting.")
        logger.info("Real data check passed (--no-synthetic mode).")
    else:
        if not check_and_generate_synthetic_data(dry_run=False):
            raise FatalError("No real data found and not in CI mode. Aborting.")

    logger.info("Pipeline initialization complete. Starting data processing steps...")
    
    # Placeholder for actual pipeline steps (T015-T022, T025, T030, etc.)
    # These will be implemented in subsequent tasks
    # For now, we log the intended flow
    steps = [
        "1. Ingest survey data (T015)",
        "2. Ingest remote sensing data (T016)",
        "3. Spatial join (T017)",
        "4. Feature engineering (T018, T018b)",
        "5. Validation and aggregation (T017c, T021)",
        "6. Regression analysis (T025)",
        "7. Sensitivity analysis (T030)",
        "8. Report generation (T032)"
    ]
    
    for step in steps:
        logger.info(step)
    
    logger.info("Pipeline execution completed successfully.")
    return 0

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Orchestrate the Climate-Smart Agriculture Optimization Pipeline."
    )
    parser.add_argument(
        "--no-synthetic",
        action="store_true",
        help="Disable automatic synthetic data generation. Fail if real data is missing."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode: verify logic without executing data processing."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level."
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    try:
        exit_code = run_pipeline(args)
        sys.exit(exit_code)
    except FatalError as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
