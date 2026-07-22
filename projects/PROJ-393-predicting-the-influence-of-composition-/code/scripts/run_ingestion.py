import logging
import sys
from pathlib import Path
from src.ingestion.ingest_pipeline import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Running Ingestion Pipeline Script...")
    
    try:
        exit_code = run_pipeline()
        logger.info(f"Ingestion script exited with code: {exit_code}")
        return exit_code
    except Exception as e:
        logger.error(f"Ingestion script failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())