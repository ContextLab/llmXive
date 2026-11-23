"""
CLI Orchestrator for the Agriculture Optimization Pipeline.

This script manages the execution flow, including:
1. Citation validation gate.
2. Data availability checks and synthetic fallback (CI mode).
3. Stage-based execution (ingest, analysis, full).
"""
import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.cli.validate_citations import main as validate_citations_main
from src.data.generators.structural_validation_generator import main as generate_synthetic_main
from src.data.processing.feature_engineering import main as feature_engineering_main
from src.data.processing.spatial_join import main as spatial_join_main
from src.data.processing.final_assembly import main as final_assembly_main
from src.analysis.run_regression import main as regression_main
from src.analysis.sensitivity_check import main as sensitivity_main
from src.services.report_generator import main as report_main
from src.utils.io_helpers import setup_logging, FatalError

def check_and_generate_synthetic_data(logger: logging.Logger) -> bool:
    """
    Checks for real data in data/raw/. If missing and CI=true,
    invokes the structural validation generator.
    Returns True if synthetic data was generated or real data exists.
    """
    data_raw_path = project_root / "data" / "raw"
    if not data_raw_path.exists():
        data_raw_path.mkdir(parents=True, exist_ok=True)

    # Check for any CSV or Parquet files in data/raw
    has_real_data = any(data_raw_path.glob("*.csv")) or any(data_raw_path.glob("*.parquet"))

    if has_real_data:
        logger.info("Real data detected in data/raw/. Proceeding with real data.")
        return True

    ci_mode = os.environ.get("CI", "false").lower() == "true"

    if ci_mode:
        logger.warning("No real data found and CI=true. Invoking structural validation generator.")
        try:
            # Generate synthetic data for structural validation
            generate_synthetic_main()
            logger.info("Structural validation data generated successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to generate synthetic data: {e}")
            raise FatalError("Synthetic data generation failed in CI mode.")
    else:
        logger.warning("No real data found. Proceeding with synthetic data for local testing.")
        try:
            generate_synthetic_main()
            logger.info("Structural validation data generated for local testing.")
            return True
        except Exception as e:
            logger.error(f"Failed to generate synthetic data: {e}")
            # In local mode, we might want to fail or proceed with partial data
            # For now, we fail to ensure data integrity
            raise FatalError("Synthetic data generation failed in local mode.")

def run_pipeline_stage_ingest(logger: logging.Logger) -> None:
    """
    Executes the ingestion pipeline:
    1. Spatial Join
    2. Feature Engineering
    3. Final Assembly (includes linkage validation logic)
    """
    logger.info("Starting Ingestion Stage...")

    # Run Spatial Join
    logger.info("Running Spatial Join...")
    spatial_join_main()

    # Run Feature Engineering
    logger.info("Running Feature Engineering...")
    feature_engineering_main()

    # Run Final Assembly (handles linkage validation and aggregation)
    logger.info("Running Final Assembly...")
    final_assembly_main()

    logger.info("Ingestion Stage completed.")

def run_pipeline_stage_analysis(logger: logging.Logger) -> None:
    """
    Executes the analysis pipeline:
    1. Regression
    2. Sensitivity Check
    3. Report Generation
    """
    logger.info("Starting Analysis Stage...")

    # Run Regression
    logger.info("Running Regression...")
    regression_main()

    # Run Sensitivity Check
    logger.info("Running Sensitivity Check...")
    sensitivity_main()

    # Run Report Generation
    logger.info("Generating Report...")
    report_main()

    logger.info("Analysis Stage completed.")

def run_pipeline_stage_full(logger: logging.Logger) -> None:
    """
    Executes the full pipeline: Ingest -> Analysis.
    """
    logger.info("Starting Full Pipeline...")
    run_pipeline_stage_ingest(logger)
    run_pipeline_stage_analysis(logger)
    logger.info("Full Pipeline completed.")

def main():
    parser = argparse.ArgumentParser(description="Agriculture Optimization Pipeline Orchestrator")
    parser.add_argument(
        "--stage",
        choices=["ingest", "analysis", "full", "dry-run"],
        default="dry-run",
        help="Pipeline stage to execute. Default: dry-run (checks only)."
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level."
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging("run_pipeline", level=args.log_level)

    # CRITICAL GATE: Validate Citations
    logger.info("Running Citation Validation Gate...")
    try:
        # The validate_citations script expects to be run as a module or script
        # We invoke its main logic directly
        validate_citations_main()
        logger.info("Citation validation passed.")
    except SystemExit as e:
        if e.code != 0:
            logger.error("Citation validation failed. Aborting pipeline.")
            sys.exit(1)
        # If it exits with 0, we continue
    except Exception as e:
        logger.error(f"Citation validation encountered an error: {e}")
        sys.exit(1)

    if args.stage == "dry-run":
        logger.info("Dry run mode: Checking environment and data availability...")
        # Check data availability
        check_and_generate_synthetic_data(logger)
        logger.info("Dry run completed successfully.")
        return

    # Check data availability before running real stages
    check_and_generate_synthetic_data(logger)

    if args.stage == "ingest":
        run_pipeline_stage_ingest(logger)
    elif args.stage == "analysis":
        run_pipeline_stage_analysis(logger)
    elif args.stage == "full":
        run_pipeline_stage_full(logger)
    else:
        logger.error(f"Unknown stage: {args.stage}")
        sys.exit(1)

if __name__ == "__main__":
    main()
