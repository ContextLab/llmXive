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
    # Simple argument parsing for quickstart compatibility
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
            # Placeholder for future download step
            logger.info("Download step not implemented in this version.")
            sys.exit(0)
        elif step == "analyze":
            # Placeholder for future analysis step
            logger.info("Analyze step not implemented in this version.")
            sys.exit(0)
        elif step == "verify":
            # Placeholder for future verification step
            logger.info("Verify step not implemented in this version.")
            sys.exit(0)
        else:
            logger.error(f"Unknown step: {step}")
            sys.exit(1)
    else:
        # Default to full thin pipeline if no arguments
        run_thin_pipeline()

if __name__ == "__main__":
    main()