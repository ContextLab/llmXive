"""
Pipeline Runner for T058 Audit.
This script orchestrates the execution of the ingestion and feature engineering pipeline
to ensure all artifacts are generated before the audit runs.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.cleaner import main as run_cleaner
from ingestion.validator import main as run_validator
from features.transformer import main as run_transformer
from features.descriptor_engine import main as run_descriptor_engine
from ingestion.verify_task_ordering import main as run_audit

logger = logging.getLogger(__name__)

def run_pipeline():
    """Execute the pipeline steps in order."""
    logger.info("Starting Pipeline Execution for T058 Audit...")
    
    # Step 1: Cleaner (T013) - Produces solder_hardness_cleaned.csv
    logger.info("Running Cleaner (T013)...")
    try:
        run_cleaner()
        logger.info("Cleaner completed successfully.")
    except Exception as e:
        logger.error(f"Cleaner failed: {e}")
        return False

    # Step 2: Validator (T014) - Produces .ingestion_status.json
    logger.info("Running Validator (T014)...")
    try:
        run_validator()
        logger.info("Validator completed successfully.")
    except Exception as e:
        logger.error(f"Validator failed: {e}")
        return False

    # Step 3: Transformer (T023b) - Produces clr_features.csv
    logger.info("Running Transformer (T023b)...")
    try:
        run_transformer()
        logger.info("Transformer completed successfully.")
    except Exception as e:
        logger.error(f"Transformer failed: {e}")
        return False

    # Step 4: Descriptor Engine (T023c) - Produces descriptors.csv
    logger.info("Running Descriptor Engine (T023c)...")
    try:
        run_descriptor_engine()
        logger.info("Descriptor Engine completed successfully.")
    except Exception as e:
        logger.error(f"Descriptor Engine failed: {e}")
        return False

    # Step 5: Audit (T058)
    logger.info("Running Audit (T058)...")
    try:
        run_audit()
        logger.info("Audit completed successfully.")
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        return False

    return True

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    success = run_pipeline()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
