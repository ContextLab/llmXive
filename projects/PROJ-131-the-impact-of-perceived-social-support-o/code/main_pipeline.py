import os
import sys
import logging
import time
import traceback
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger

def run_pipeline():
    logger = get_logger(__name__)
    logger.info("Starting the pipeline...")

    # Step 1: Verify Spec Alignment (T072a)
    logger.info("Step 1: Verifying Spec Alignment (T072a)...")
    try:
        from data.verify_spec_alignment import main as verify_spec_main
        verify_spec_main()
    except Exception as e:
        logger.error(f"Spec alignment verification failed: {e}")
        raise

    # Step 2: Initialize Logging (T017)
    logger.info("Step 2: Initializing Logging (T017)...")
    # Logging is already initialized at the top, but we can add specific handlers here if needed.

    # Step 3: Ingestion (T012)
    logger.info("Step 3: Running Ingestion (T012)...")
    try:
        from data.ingestion import main as ingestion_main
        ingestion_main()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise

    # Step 4: Preprocessing (T013a-Config, T013a-Exec, T013a-Check, T013b, T013c, T013d)
    logger.info("Step 4: Running Preprocessing (T013)...")
    try:
        from data.preprocessing import main as preprocessing_main
        preprocessing_main()
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

    # Step 5: Cohort Construction (T014, T015, T016)
    logger.info("Step 5: Constructing Cohort (T014-T016)...")
    try:
        from data.cohort import main as cohort_main
        cohort_main()
    except Exception as e:
        logger.error(f"Cohort construction failed: {e}")
        raise

    # Step 6: Modeling (T020, T021, T022, T023, T024)
    logger.info("Step 6: Running Modeling (T020-T024)...")
    try:
        from analysis.models import main as models_main
        models_main()
    except Exception as e:
        logger.error(f"Modeling failed: {e}")
        raise

    # Step 7: Sensitivity Analysis (T027a, T027b, T028, T029)
    logger.info("Step 7: Running Sensitivity Analysis (T027-T029)...")
    try:
        from analysis.sensitivity import main as sensitivity_main
        sensitivity_main()
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

    # Step 8: Results Generation (T024b, T025)
    logger.info("Step 8: Generating Results (T024b-T025)...")
    try:
        from analysis.results import main as results_main
        results_main()
    except Exception as e:
        logger.error(f"Results generation failed: {e}")
        raise

    logger.info("Pipeline completed successfully.")

def main():
    logger = get_logger(__name__)
    try:
        run_pipeline()
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
