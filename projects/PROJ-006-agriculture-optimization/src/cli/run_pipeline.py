import argparse
import logging
import os
import sys
import shutil
from pathlib import Path

from src.data.generators.synthetic_generator import SyntheticDataGenerator, main as generate_synthetic_main
from src.data.processing.feature_engineering import run_feature_engineering
from src.data.processing.spatial_join import verify_linkage_and_trigger_aggregation
from src.analysis.run_regression import main as run_regression_main
from src.analysis.sensitivity_check import main as run_sensitivity_main
from src.services.report_generator import generate_report
from src.utils.io_helpers import setup_logging, FatalError
from src.config.constants import PROJECT_ROOT

logger = logging.getLogger(__name__)

def check_and_generate_synthetic_data():
    """
    Checks for real data in data/raw/. If missing and CI=true, invokes the synthetic generator.
    """
    raw_data_path = PROJECT_ROOT / "data" / "raw"
    if not raw_data_path.exists() or not any(raw_data_path.iterdir()):
        if os.environ.get("CI") == "true":
            logger.info("No real data found in data/raw/. Invoking synthetic generator (CI mode).")
            # Call the synthetic generator main directly to populate data
            generate_synthetic_main()
        else:
            raise FatalError("No real data found in data/raw/ and CI environment variable is not set. "
                             "Please provide real data or run with CI=true.")
    else:
        logger.info("Real data detected in data/raw/. Proceeding with pipeline.")

def run_pipeline(dry_run=False):
    """
    Orchestrates the full pipeline:
    1. Check/Generate Data
    2. Spatial Join & Aggregation
    3. Feature Engineering
    4. Regression Analysis
    5. Sensitivity Check
    6. Report Generation
    """
    if dry_run:
        logger.info("Dry run: Validating structure and configuration only.")
        # Basic checks
        assert (PROJECT_ROOT / "contracts").exists(), "Contracts directory missing"
        assert (PROJECT_ROOT / "data").exists(), "Data directory missing"
        logger.info("Dry run passed.")
        return

    logger.info("Starting pipeline execution...")

    # Step 1: Data Availability
    check_and_generate_synthetic_data()

    # Step 2 & 3: Spatial Join and Feature Engineering
    # Note: These functions are designed to handle the logic of linking and aggregating
    logger.info("Running spatial join and linkage validation...")
    # We assume the data collectors have already populated data/raw/ with the necessary CSVs
    # The spatial_join module handles the heavy lifting of linking and triggering aggregation
    verify_linkage_and_trigger_aggregation()

    logger.info("Running feature engineering...")
    run_feature_engineering()

    # Step 4: Regression Analysis
    logger.info("Running regression analysis...")
    run_regression_main()

    # Step 5: Sensitivity Check
    logger.info("Running sensitivity analysis...")
    run_sensitivity_main()

    # Step 6: Report Generation
    logger.info("Generating final report...")
    generate_report()

    logger.info("Pipeline execution completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Run the Climate-Smart Agriculture Optimization Pipeline.")
    parser.add_argument("--no-synthetic", action="store_true", help="Fail if real data is missing.")
    parser.add_argument("--dry-run", action="store_true", help="Validate configuration without running full pipeline.")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO", help="Logging level.")

    args = parser.parse_args()

    setup_logging(level=args.log_level)

    if args.no_synthetic:
        # Override CI behavior if explicitly requested
        os.environ["CI"] = "false"

    try:
        run_pipeline(dry_run=args.dry_run)
    except FatalError as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
