import logging
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add project root to path if running from subdirectory
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config.environment import get_local_paths, ensure_directories
from analysis.load_data import main as load_data_main
from analysis.preprocess import main as preprocess_main
from analysis.merge_metadata import main as merge_metadata_main
from analysis.model import main as model_main
from analysis.sensitivity import main as sensitivity_main
from analysis.plot_final_figures import main as plot_main
from analysis.write_dataset import main as write_dataset_main

def setup_logging():
    """Configure logging to file and console."""
    paths = get_local_paths()
    ensure_directories([paths['logs']])
    
    log_file = paths['logs'] / 'pipeline.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('pipeline')

class AnalysisTimer:
    def __init__(self, logger):
        self.logger = logger
        self.start_time = None
        self.total_time = 0

    def start(self):
        self.start_time = time.time()
        self.logger.info("Pipeline started.")

    def stop(self):
        self.total_time = time.time() - self.start_time
        self.logger.info(f"Pipeline completed in {self.total_time:.2f} seconds.")
        return self.total_time

def run_pipeline():
    """Execute the full analysis pipeline."""
    logger = setup_logging()
    timer = AnalysisTimer(logger)
    
    try:
        timer.start()
        
        # Phase 0: Data Availability Gate (Implicitly handled in load_data/validation)
        # Note: T007A logic is embedded in load_data.py or run before this if needed.
        
        # Phase 3: User Story 1 - Data Acquisition & Preprocessing
        logger.info("--- Phase 3: Data Acquisition & Preprocessing ---")
        load_data_main()
        preprocess_main()
        merge_metadata_main() # T018: Merge metadata
        write_dataset_main() # T020: Write final dataset (ensures checksum)
        
        # Phase 4: User Story 2 - Statistical Modeling
        logger.info("--- Phase 4: Statistical Modeling ---")
        model_main()
        
        # Phase 5: User Story 3 - Sensitivity Analysis
        logger.info("--- Phase 5: Sensitivity Analysis ---")
        sensitivity_main()
        plot_main()
        
        timer.stop()
        logger.info("Pipeline finished successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    run_pipeline()
