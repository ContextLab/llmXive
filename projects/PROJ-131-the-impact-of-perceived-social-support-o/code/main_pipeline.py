import os
import sys
import logging
from pathlib import Path
from typing import Optional

from logger import get_logger
from data.ingestion import main as ingestion_main
from data.preprocessing import main as preprocessing_main
from data.cohort import main as cohort_main
from analysis.validation import main as validation_main
from analysis.models import main as models_main
from analysis.bootstrap_ci import main as bootstrap_main
from analysis.fdr_correction import main as fdr_main
from analysis.sensitivity import main as sensitivity_main
from analysis.sensitivity_compare import main as sensitivity_compare_main
from analysis.results import main as results_main

# Ensure project root is in path for relative imports if running as script
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

logger = get_logger(__name__)

def run_pipeline(
    skip_ingestion: bool = False,
    skip_preprocessing: bool = False,
    skip_cohort: bool = False,
    skip_validation: bool = False,
    skip_modeling: bool = False,
    skip_sensitivity: bool = False,
    skip_reporting: bool = False,
    force: bool = False
) -> bool:
    """
    Orchestrates the full research pipeline:
    Ingestion -> Preprocessing -> Matching -> Validation -> Modeling -> Sensitivity -> Reporting.

    Args:
        skip_ingestion: Skip data download and loading.
        skip_preprocessing: Skip cleaning and imputation.
        skip_cohort: Skip propensity score matching and weighting.
        skip_validation: Skip balance checks on the cohort.
        skip_modeling: Skip OLS regression and bootstrapping.
        skip_sensitivity: Skip sensitivity analysis.
        skip_reporting: Skip final report generation.
        force: Force re-run even if outputs exist (logic handled by downstream modules).

    Returns:
        True if pipeline completes successfully, False otherwise.
    """
    logger.info("Starting research pipeline execution...")
    logger.info(f"Working directory: {_project_root}")

    try:
        # Phase 1: Ingestion
        if not skip_ingestion:
            logger.info("=== Phase 1: Data Ingestion ===")
            ingestion_main()
        else:
            logger.info("Skipping Data Ingestion.")

        # Phase 2: Preprocessing
        if not skip_preprocessing:
            logger.info("=== Phase 2: Preprocessing ===")
            preprocessing_main()
        else:
            logger.info("Skipping Preprocessing.")

        # Phase 3: Cohort Construction (Matching/Weighting)
        if not skip_cohort:
            logger.info("=== Phase 3: Cohort Construction ===")
            cohort_main()
        else:
            logger.info("Skipping Cohort Construction.")

        # Phase 4: Validation
        if not skip_validation:
            logger.info("=== Phase 4: Cohort Validation ===")
            validation_main()
        else:
            logger.info("Skipping Cohort Validation.")

        # Phase 5: Modeling (OLS + Bootstrap + FDR)
        if not skip_modeling:
            logger.info("=== Phase 5: Modeling & Hypothesis Testing ===")
            # Run OLS models
            models_main()
            # Run Bootstrap CIs
            bootstrap_main()
            # Apply FDR Correction
            fdr_main()
        else:
            logger.info("Skipping Modeling.")

        # Phase 6: Sensitivity Analysis
        if not skip_sensitivity:
            logger.info("=== Phase 6: Sensitivity Analysis ===")
            sensitivity_main()
            sensitivity_compare_main()
        else:
            logger.info("Skipping Sensitivity Analysis.")

        # Phase 7: Reporting
        if not skip_reporting:
            logger.info("=== Phase 7: Reporting ===")
            results_main()
        else:
            logger.info("Skipping Reporting.")

        logger.info("Pipeline execution completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Pipeline execution failed with error: {e}", exc_info=True)
        return False

def main():
    """Entry point for the pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Run the Social Support Resilience Pipeline")
    parser.add_argument("--skip-ingestion", action="store_true", help="Skip data ingestion")
    parser.add_argument("--skip-preprocessing", action="store_true", help="Skip preprocessing")
    parser.add_argument("--skip-cohort", action="store_true", help="Skip cohort construction")
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation")
    parser.add_argument("--skip-modeling", action="store_true", help="Skip modeling")
    parser.add_argument("--skip-sensitivity", action="store_true", help="Skip sensitivity analysis")
    parser.add_argument("--skip-reporting", action="store_true", help="Skip reporting")
    parser.add_argument("--force", action="store_true", help="Force re-run")

    args = parser.parse_args()

    success = run_pipeline(
        skip_ingestion=args.skip_ingestion,
        skip_preprocessing=args.skip_preprocessing,
        skip_cohort=args.skip_cohort,
        skip_validation=args.skip_validation,
        skip_modeling=args.skip_modeling,
        skip_sensitivity=args.skip_sensitivity,
        skip_reporting=args.skip_reporting,
        force=args.force
    )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()