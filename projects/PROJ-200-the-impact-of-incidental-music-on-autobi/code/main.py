import sys
import logging
from config import ensure_directories, get_project_root
from utils import setup_logging, get_logger
import data_ingestion
import aggregation
import modeling

logger = get_logger(__name__)

def run_thin_pipeline():
    logger.info("Executing Thin End-to-End Pipeline (T003)...")
    ensure_directories()
    
    logger.info("Step 1: Ingestion")
    data_ingestion.main()
    
    logger.info("Step 2: Aggregation")
    aggregation.main()
    
    logger.info("Step 3: Modeling")
    modeling.main()
    
    logger.info("Thin pipeline completed successfully.")

def main():
    setup_logging()
    run_thin_pipeline()

if __name__ == "__main__":
    main()
