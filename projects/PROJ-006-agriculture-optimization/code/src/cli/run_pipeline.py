"""
CLI Orchestrator for the Climate-Smart Agriculture Optimization Pipeline.

This script coordinates the execution of data ingestion, processing, analysis,
and reporting stages. It handles synthetic data generation for CI environments
when real data is unavailable and enforces citation validation gates.
"""
import argparse
import logging
import os
import sys
import shutil
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.cli.validate_citations import main as validate_citations_main
from src.data.generators.structural_validation_generator import main as generate_structural_main
from src.data.processing.feature_engineering import main as feature_engineering_main
from src.utils.io_helpers import setup_logging, FatalError

# Configure logging
logger = setup_logging("run_pipeline")

def check_and_generate_synthetic_data():
    """
    Check for real data in data/raw/. If missing and in CI mode,
    invoke the structural validation generator.
    """
    data_raw_dir = project_root / "data" / "raw"
    has_real_data = any(data_raw_dir.iterdir()) if data_raw_dir.exists() else False

    ci_mode = os.environ.get("CI", "false").lower() == "true"

    if not has_real_data:
        if ci_mode:
            logger.info("CI mode active: No real data found. Invoking structural validation generator.")
            try:
                generate_structural_main()
                logger.info("Structural validation data generated successfully.")
            except Exception as e:
                logger.error(f"Failed to generate structural validation data: {e}")
                raise FatalError("Synthetic data generation failed in CI mode.")
        else:
            logger.warning("No real data found and CI=false. Proceeding with synthetic data for local testing.")
            try:
                generate_structural_main()
                logger.info("Structural validation data generated for local testing.")
            except Exception as e:
                logger.error(f"Failed to generate structural validation data: {e}")
                raise FatalError("Synthetic data generation failed.")
    else:
        logger.info("Real data detected in data/raw/. Skipping synthetic generation.")

def run_pipeline_stage_ingest():
    """
    Execute the ingestion stage.
    This includes generating synthetic data if needed and running feature engineering.
    """
    logger.info("Starting Ingestion Stage.")
    
    # Step 1: Ensure data exists (generate if missing/CI)
    check_and_generate_synthetic_data()

    # Step 2: Run Feature Engineering to derive metrics
    # Note: The structural validation generator creates raw CSVs.
    # Feature engineering reads them and creates the analysis dataset.
    try:
        feature_engineering_main()
        logger.info("Feature engineering completed.")
    except Exception as e:
        logger.error(f"Feature engineering failed: {e}")
        raise

def run_pipeline_stage_analysis():
    """
    Execute the analysis stage (regression).
    """
    logger.info("Starting Analysis Stage.")
    # Import here to avoid circular dependencies if not needed for ingest
    from src.analysis.run_regression import main as run_regression_main
    try:
        run_regression_main()
        logger.info("Regression analysis completed.")
    except Exception as e:
        logger.error(f"Regression analysis failed: {e}")
        raise

def run_pipeline_stage_full():
    """
    Execute the full pipeline: Ingest -> Analysis -> Sensitivity -> Report.
    """
    logger.info("Starting Full Pipeline.")
    run_pipeline_stage_ingest()
    run_pipeline_stage_analysis()
    
    # Sensitivity Check
    logger.info("Starting Sensitivity Analysis.")
    from src.analysis.sensitivity_check import main as sensitivity_main
    try:
        sensitivity_main()
        logger.info("Sensitivity analysis completed.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

    # Report Generation
    logger.info("Generating Final Report.")
    from src.services.report_generator import main as report_main
    try:
        report_main()
        logger.info("Final report generated.")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description="CLI Orchestrator for Climate-Smart Agriculture Pipeline"
    )
    parser.add_argument(
        "--stage",
        type=str,
        choices=["ingest", "analysis", "full", "dry-run"],
        default="dry-run",
        help="Pipeline stage to execute."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run (validate setup without full execution)."
    )
    parser.add_argument(
        "--no-citation-check",
        action="store_true",
        help="Skip the citation validation gate (not recommended)."
    )

    args = parser.parse_args()

    # CRITICAL GATE: Citation Validation
    # This check is independent of data availability.
    if not args.no_citation_check:
        logger.info("Running Citation Validation Gate...")
        try:
            # validate_citations_main returns 0 on success, non-zero on failure
            # We need to capture the exit code logic. 
            # The function likely sys.exits, so we wrap in try/except SystemExit
            try:
                validate_citations_main()
            except SystemExit as e:
                if e.code != 0:
                    logger.error("Citation validation failed. Aborting pipeline.")
                    sys.exit(1)
                # If exit code is 0, continue
        except Exception as e:
            logger.error(f"Citation validation check encountered an error: {e}")
            sys.exit(1)
        logger.info("Citation validation passed.")

    if args.dry_run:
        logger.info("Dry run mode: Validating pipeline configuration and dependencies.")
        # Check imports
        try:
            from src.data.generators.structural_validation_generator import StructuralValidationGenerator
            from src.data.processing.feature_engineering import check_and_aggregate_if_needed
            from src.analysis.run_regression import run_regression_models
            logger.info("All required modules imported successfully.")
            logger.info("Dry run complete. Exiting.")
            sys.exit(0)
        except ImportError as e:
            logger.error(f"Import error during dry run: {e}")
            sys.exit(1)

    if args.stage == "ingest":
        run_pipeline_stage_ingest()
    elif args.stage == "analysis":
        run_pipeline_stage_analysis()
    elif args.stage == "full":
        run_pipeline_stage_full()
    else:
        logger.warning("No valid stage specified. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    main()
