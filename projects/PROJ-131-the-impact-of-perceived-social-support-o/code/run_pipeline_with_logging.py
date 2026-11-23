"""
Pipeline Runner with Logging.
"""
import sys
import traceback
from logger import get_logger
from data.ingestion import main as ingestion_main
from data.preprocessing import main as preprocessing_main
from data.cohort import main as cohort_main

logger = get_logger()

def run_pipeline():
    try:
        logger.info("Starting Pipeline...")
        ingestion_main()
        preprocessing_main()
        cohort_main()
        logger.info("Pipeline completed.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        traceback.print_exc()
        raise
