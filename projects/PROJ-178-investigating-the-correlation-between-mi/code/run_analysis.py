import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from config.environment import get_local_paths

def setup_logging():
    """Setup logging configuration for the analysis pipeline."""
    log_dir = get_local_paths()['logs']
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

class AnalysisTimer:
    """Timer to track execution time of analysis stages."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger = logging.getLogger(__name__)
        logger.info(f"Starting {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time
        logger = logging.getLogger(__name__)
        logger.info(f"Completed {self.name} in {elapsed:.2f} seconds")
        return False

def run_pipeline():
    """
    Run the complete analysis pipeline.
    This orchestrates all tasks from T018 to T020.
    """
    logger = setup_logging()
    logger.info("Starting mito-aging correlation analysis pipeline")
    
    try:
        # Step 1: Merge metadata (T018)
        with AnalysisTimer("Metadata Merge (T018)"):
            from analysis.merge_metadata import main as merge_main
            merge_main()
        
        # Step 2: Clean dataset - apply exclusion logic (T019)
        with AnalysisTimer("Dataset Cleaning (T019)"):
            from analysis.clean_dataset import main as clean_main
            clean_main()
        
        # Step 3: Write processed dataset with checksum (T020)
        with AnalysisTimer("Dataset Writing (T020)"):
            from analysis.write_dataset import main as write_main
            write_main()
        
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == '__main__':
    run_pipeline()