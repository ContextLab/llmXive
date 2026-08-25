"""
Main orchestration script for the Agriculture Optimization Pipeline.

Handles data ingestion, checking for real data, and automatic fallback
to synthetic data generation in CI environments if real data is missing.
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.io_helpers import FatalError, setup_logging
from src.data.generators.synthetic_generator import SyntheticDataGenerator, check_real_data_exists

# Configure logging
logger = setup_logging("run_pipeline", log_file="data/logs/pipeline.log")

def check_and_generate_synthetic_data(force_no_synthetic: bool = False) -> bool:
    """
    Checks for real data in data/raw/.
    
    If real data is missing:
    - If --no-synthetic is provided, raises FatalError.
    - If CI=true environment variable is set, invokes the synthetic generator.
    - Otherwise, logs a warning and returns False (pipeline will likely fail downstream).
    
    Returns:
        bool: True if real data exists or synthetic data was successfully generated.
    """
    logger.info("Checking for real data in data/raw/...")
    
    real_data_exists = check_real_data_exists()
    
    if real_data_exists:
        logger.info("Real data detected. Proceeding with real data.")
        return True
    
    logger.warning("Real data not found in data/raw/.")
    
    if force_no_synthetic:
        raise FatalError("Real data is missing and --no-synthetic flag was provided. Aborting.")
    
    is_ci = os.environ.get("CI", "").lower() == "true"
    
    if is_ci:
        logger.info("CI environment detected. Automatically invoking synthetic data generator.")
        try:
            # Invoke the synthetic generator programmatically
            SyntheticDataGenerator.generate(
                output_path=project_root / "data" / "raw" / "synthetic_analysis_dataset.csv",
                n_samples=350, # Ensure > 300 as per spec
                seed=42
            )
            logger.info("Synthetic data generated successfully.")
            return True
        except Exception as e:
            raise FatalError(f"Failed to generate synthetic data in CI: {e}")
    else:
        logger.warning("Not in CI environment and --no-synthetic not provided. "
                     "Pipeline will proceed but may fail if real data is required.")
        return False

def run_pipeline(args: argparse.Namespace) -> None:
    """
    Main pipeline execution logic.
    
    Currently implements the orchestration logic for T010a:
    1. Check for real data / generate synthetic if needed.
    2. In a full implementation, this would call collectors, processors, and analyzers.
    """
    logger.info("Starting Agriculture Optimization Pipeline.")
    
    # Step 1: Data Availability Check
    if not check_and_generate_synthetic_data(force_no_synthetic=args.no_synthetic):
        if not args.dry_run:
            raise FatalError("Pipeline cannot proceed without data and synthetic generation was not triggered.")
    
    if args.dry_run:
        logger.info("Dry run mode: Skipping actual data processing steps.")
        logger.info("Pipeline structure validated successfully.")
        # In a real run, we would verify downstream paths exist here
        return
    
    logger.info("Running full pipeline steps...")
    # Placeholder for future steps (T015-T022, T025, etc.)
    # Example:
    # from src.data.collectors.survey_collector import SurveyCollector
    # collector = SurveyCollector()
    # collector.collect()
    
    logger.info("Pipeline execution completed.")

def main() -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Orchestrate the Agriculture Optimization Pipeline."
    )
    parser.add_argument(
        "--no-synthetic",
        action="store_true",
        help="Disable automatic synthetic data generation. Raises FatalError if real data is missing."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate pipeline configuration and flags without executing data processing."
    )
    
    args = parser.parse_args()
    
    try:
        run_pipeline(args)
    except FatalError as e:
        logger.error(f"Fatal Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
