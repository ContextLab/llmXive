import logging
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent))

from config import init_logger
from ingest import main as run_ingest
from preprocess import main as run_preprocess
from analysis import main as run_analysis
from report import main as run_report

def main():
    logger = init_logger()
    logger.info("Starting full pipeline")
    
    try:
        logger.info("Step 1: Ingest")
        run_ingest()
        
        logger.info("Step 2: Preprocess")
        run_preprocess()
        
        logger.info("Step 3: Analysis")
        run_analysis()
        
        logger.info("Step 4: Report")
        run_report()
        
        logger.info("Pipeline completed successfully")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
