"""
Main pipeline entry point for the llmXive project.
Orchestrates modular steps: Ingestion -> Preprocessing -> Cohort Construction -> Validation -> Modeling -> Sensitivity -> Reporting.
"""
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
from analysis.save_regression_results import main as save_regression_main
from analysis.results import main as results_main
from analysis.sensitivity import main as sensitivity_main
from analysis.run_sensitivity_comparison import main as sensitivity_comparison_main
from analysis.save_sensitivity_results import main as save_sensitivity_main

# Ensure project root is in path for imports if running from code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = get_logger("main_pipeline")

def run_pipeline(
    skip_ingestion: bool = False,
    skip_preprocessing: bool = False,
    skip_cohort: bool = False,
    skip_validation: bool = False,
    skip_modeling: bool = False,
    skip_sensitivity: bool = False,
    skip_reporting: bool = False
) -> bool:
    """
    Execute the full research pipeline sequentially.
    
    Args:
        skip_ingestion: Skip data download/ingestion if data already exists.
        skip_preprocessing: Skip preprocessing steps.
        skip_cohort: Skip synthetic cohort construction.
        skip_validation: Skip validation checks (runs anyway for logging).
        skip_modeling: Skip regression modeling and bootstrapping.
        skip_sensitivity: Skip sensitivity analysis.
        skip_reporting: Skip final report generation.
    
    Returns:
        True if pipeline completes successfully, False otherwise.
    """
    logger.info("Starting main pipeline execution...")
    logger.info(f"Project Root: {PROJECT_ROOT}")

    try:
        # 1. Ingestion
        if not skip_ingestion:
            logger.info("Step 1: Data Ingestion")
            ingestion_main()
        else:
            logger.info("Step 1: Data Ingestion (Skipped)")

        # 2. Preprocessing
        if not skip_preprocessing:
            logger.info("Step 2: Preprocessing & Imputation")
            preprocessing_main()
        else:
            logger.info("Step 2: Preprocessing (Skipped)")

        # 3. Cohort Construction
        if not skip_cohort:
            logger.info("Step 3: Synthetic Cohort Construction")
            cohort_main()
        else:
            logger.info("Step 3: Cohort Construction (Skipped)")

        # 4. Validation
        if not skip_validation:
            logger.info("Step 4: Synthetic Cohort Validation")
            # Validation is critical; we run it even if other steps are skipped
            # to ensure data quality before modeling.
            validation_main()
        else:
            logger.info("Step 4: Validation (Skipped)")

        # 5. Modeling (OLS + Bootstrap)
        if not skip_modeling:
            logger.info("Step 5: Regression Modeling & Bootstrapping")
            models_main()
            bootstrap_main()
        else:
            logger.info("Step 5: Modeling (Skipped)")

        # 6. FDR Correction & Save Regression Results
        if not skip_modeling:
            logger.info("Step 6: FDR Correction & Saving Regression Results")
            fdr_main()
            save_regression_main()
        else:
            logger.info("Step 6: FDR & Save Results (Skipped)")

        # 7. Sensitivity Analysis
        if not skip_sensitivity:
            logger.info("Step 7: Sensitivity Analysis")
            sensitivity_main()
            sensitivity_comparison_main()
            save_sensitivity_main()
        else:
            logger.info("Step 7: Sensitivity Analysis (Skipped)")

        # 8. Reporting
        if not skip_reporting:
            logger.info("Step 8: Generating Summary Report")
            results_main()
        else:
            logger.info("Step 8: Reporting (Skipped)")

        logger.info("Pipeline execution completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        return False

def main():
    """CLI entry point for the pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the full research pipeline.")
    parser.add_argument("--skip-ingestion", action="store_true", help="Skip data ingestion")
    parser.add_argument("--skip-preprocessing", action="store_true", help="Skip preprocessing")
    parser.add_argument("--skip-cohort", action="store_true", help="Skip cohort construction")
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation")
    parser.add_argument("--skip-modeling", action="store_true", help="Skip modeling")
    parser.add_argument("--skip-sensitivity", action="store_true", help="Skip sensitivity analysis")
    parser.add_argument("--skip-reporting", action="store_true", help="Skip reporting")
    
    args = parser.parse_args()
    
    success = run_pipeline(
        skip_ingestion=args.skip_ingestion,
        skip_preprocessing=args.skip_preprocessing,
        skip_cohort=args.skip_cohort,
        skip_validation=args.skip_validation,
        skip_modeling=args.skip_modeling,
        skip_sensitivity=args.skip_sensitivity,
        skip_reporting=args.skip_reporting
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()