import sys
import logging
import pyarrow # Import pyarrow first to avoid pandas compatibility issues
import pandas as pd
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
    if len(sys.argv) > 1 and sys.argv[1] == "--step":
        if len(sys.argv) < 3:
            logger.error("No step specified after --step")
            sys.exit(1)
        step = sys.argv[2]
        if step == "ingest":
            ensure_directories()
            data_ingestion.main()
            sys.exit(0)
        elif step == "download":
            logger.info("Download step: Handled within ingestion for thin pipeline.")
            sys.exit(0)
        elif step == "analyze":
            ensure_directories()
            modeling.main()
            sys.exit(0)
        elif step == "verify":
            logger.info("Verify step: Handled by external tests.")
            sys.exit(0)
        else:
            logger.error(f"Unknown step: {step}")
            sys.exit(1)
    elif len(sys.argv) > 1 and sys.argv[1] == "--full-run":
        run_thin_pipeline()
    else:
        run_thin_pipeline()

if __name__ == "__main__":
    main()
