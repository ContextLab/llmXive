import os
import sys
import time
import signal
import logging
import json
from pathlib import Path
from data.download import download_oqmd_dataset, main as download_main
from data.preprocess import main as preprocess_main
from data.generate_validation_report import main as validation_main
from utils.timing_logger import TimingLogger

# Global timeout
TIMEOUT_HOURS = 5.0
TIMEOUT_SECONDS = TIMEOUT_HOURS * 3600

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Pipeline execution timed out!")

def setup_logging(log_path: str = "logs/pipeline.log"):
    """Setup logging configuration."""
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_pipeline():
    """Execute the full pipeline with timeout enforcement."""
    logger = setup_logging()
    logger.info("Starting pipeline execution...")
    
    # Set up signal handler for timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)
    
    timing_logger = TimingLogger(logger)
    
    try:
        # Step 1: Download data
        timing_logger.start("download")
        download_main()
        timing_logger.end("download")
        
        # Step 2: Preprocess data
        timing_logger.start("preprocess")
        preprocess_main()
        timing_logger.end("preprocess")
        
        # Step 3: Generate validation report
        timing_logger.start("validation_report")
        validation_main()
        timing_logger.end("validation_report")
        
        # Step 4: Model training and UQ (placeholder for now)
        # This will be implemented in subsequent tasks
        logger.info("Data preparation complete. Model training phase pending.")
        
        timing_logger.finish()
        timing_logger.save("results/timing_report.json")
        
        logger.info("Pipeline execution completed successfully.")
        
    except TimeoutError as e:
        logger.error(f"Pipeline timed out: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        return 1
    finally:
        signal.alarm(0)  # Cancel the alarm
        
    return 0

def main():
    """Main entry point."""
    exit_code = run_pipeline()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
