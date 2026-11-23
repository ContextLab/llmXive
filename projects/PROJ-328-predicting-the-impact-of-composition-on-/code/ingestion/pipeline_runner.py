"""
Pipeline runner to orchestrate the ingestion and cleaning tasks.
Ensures T013 (cleaner) is executed and produces required outputs.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion.cleaner import main as run_cleaner
from ingestion.validator import main as run_validator

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def run_pipeline():
    """
    Execute the full ingestion and cleaning pipeline.
    
    Steps:
    1. Run cleaner (T013) to produce solder_hardness_cleaned.csv and .ingestion_status.json
    2. Run validator (T014) to validate the cleaned data
    """
    logger.info("Starting ingestion pipeline")
    
    try:
        # Step 1: Run cleaner (T013)
        logger.info("Executing T013: Data Cleaning")
        run_cleaner()
        
        # Step 2: Run validator (T014)
        logger.info("Executing T014: Data Validation")
        run_validator()
        
        logger.info("Ingestion pipeline completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return False

def main():
    """Main entry point."""
    success = run_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
