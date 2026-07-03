import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.environment import ensure_directories, get_ftp_urls, get_local_paths

def setup_logging():
    """Configures logging to file and console."""
    ensure_directories()
    log_file = Path(get_local_paths()["logs_dir"]) / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
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
    def __init__(self, task_name):
        self.task_name = task_name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        logging.info(f"Starting task: {self.task_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        if exc_type is not None:
            logging.error(f"Task {self.task_name} failed after {duration:.2f}s")
        else:
            logging.info(f"Task {self.task_name} completed in {duration:.2f}s")

def run_pipeline():
    """Executes the full analysis pipeline."""
    logger = setup_logging()
    logger.info("Pipeline started")
    
    # Import tasks
    from analysis.load_data import main as task_load_data
    from analysis.preprocess import main as task_preprocess
    from analysis.merge_metadata import main as task_merge
    from analysis.model import main as task_model
    from analysis.sensitivity import main as task_sensitivity
    from analysis.sensitivity_report import main as task_report
    from analysis.visualize import main as task_visualize

    try:
        # Phase 1: Data Acquisition
        with AnalysisTimer("T012: Load Data"):
            task_load_data()
        
        # Phase 2: Preprocessing
        with AnalysisTimer("T014-T017: Preprocess"):
            task_preprocess()
        
        # Phase 3: Merge
        with AnalysisTimer("T018-T020: Merge Metadata"):
            task_merge()
        
        # Phase 4: Modeling
        with AnalysisTimer("T023-T025: Statistical Modeling"):
            task_model()
        
        # Phase 5: Sensitivity
        with AnalysisTimer("T032-T037: Sensitivity Analysis"):
            task_sensitivity()
        
        # Phase 6: Reporting
        with AnalysisTimer("T038: Write Sensitivity Report"):
            task_report()
        
        # Phase 7: Visualization
        with AnalysisTimer("T037: Generate Plots"):
            task_visualize()

        logger.info("Pipeline completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(run_pipeline())