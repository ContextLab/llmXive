"""
Main Pipeline Orchestrator for PROJ-131.

Executes the full research pipeline end-to-end:
1. Data Ingestion (T012)
2. Preprocessing (T013a-d)
3. Cohort Construction (T014)
4. Validation (T015)
5. Platform Verification (T012b) - Explicitly called here to ensure T012b is run
6. Modeling (T020-T024)
7. Sensitivity Analysis (T027a-T029)
8. Comparison (T028)
9. Reporting (T025)
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/pipeline_run.log')
    ]
)
logger = logging.getLogger(__name__)

# Ensure project root is in path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def run_pipeline():
    """Orchestrate the full pipeline execution."""
    logger.info("="*50)
    logger.info("Starting Research Pipeline: PROJ-131")
    logger.info("="*50)
    
    start_time = time.time()

    try:
        # 1. Data Ingestion
        logger.info("Step 1: Data Ingestion (T012)")
        from data.ingestion import main as ingestion_main
        ingestion_main()
        
        # 2. Preprocessing
        logger.info("Step 2: Preprocessing (T013a-d)")
        from data.preprocessing import main as preprocessing_main
        preprocessing_main()

        # 3. Cohort Construction
        logger.info("Step 3: Cohort Construction (T014)")
        from data.cohort import main as cohort_main
        cohort_main()

        # 4. Validation (T015)
        logger.info("Step 4: Validation (T015)")
        from analysis.validation import main as validation_main
        validation_main()

        # 5. Platform Verification (T012b)
        # Explicitly run T012b here to ensure platform status is updated before sensitivity
        logger.info("Step 5: Platform Verification (T012b)")
        from data.verify_columns import main as verify_columns_main
        verify_columns_main()

        # 6. Modeling (T020-T024)
        logger.info("Step 6: Modeling & Bootstrap (T020-T024)")
        from analysis.models import main as models_main
        models_main()
        
        # Save Regression Results
        logger.info("Step 6b: Saving Regression Results (T024)")
        from analysis.save_regression_results import main as save_regression_main
        save_regression_main()

        # 7. Sensitivity Analysis (T027a-T029)
        logger.info("Step 7: Sensitivity Analysis (T027a-T029)")
        from analysis.sensitivity import main as sensitivity_main
        sensitivity_main()
        
        # Save Sensitivity Results
        logger.info("Step 7b: Saving Sensitivity Results (T029)")
        from analysis.save_sensitivity_results import main as save_sensitivity_main
        save_sensitivity_main()

        # 8. Comparison (T028)
        logger.info("Step 8: Coefficient Comparison (T028)")
        from analysis.run_sensitivity_comparison import main as comparison_main
        comparison_main()

        # 9. Reporting (T025)
        logger.info("Step 9: Generate Reports (T025)")
        from analysis.results import main as results_main
        results_main()

        # 10. FDR Correction (T023)
        # Note: FDR is often integrated into the save_regression step, but ensuring explicit call if needed
        # The save_regression_results task (T024) usually handles the merge and FDR.
        # If a separate step is required by spec T023, it would be here.
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info("="*50)
        logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        logger.exception("Traceback:")
        raise

def main():
    """Entry point."""
    run_pipeline()

if __name__ == "__main__":
    main()
