"""
Orchestration Script for the Doomscrolling Anxiety Analysis Pipeline.

Executes the pipeline in order: ingest -> clean -> model -> viz.
Handles exceptions and logs to outputs/analysis.log.
"""
import sys
import logging
import time
from pathlib import Path

# Import pipeline modules
from config import load_config, ensure_directories, log_seed_status, verify_and_apply_seed
from ingest import main as ingest_main
from clean import main as clean_main
from model import main as model_main
from viz import main as viz_main
from robustness import main as robustness_main
from report_generator import main as report_main

def setup_logger():
    """Configure logging to file and console."""
    log_dir = Path("outputs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "analysis.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    start_time = time.time()
    logger = setup_logger()
    logger.info("="*50)
    logger.info("Starting Doomscrolling Anxiety Analysis Pipeline")
    logger.info("="*50)

    try:
        # 1. Configuration
        logger.info("Loading configuration...")
        config = load_config()
        ensure_directories()
        verify_and_apply_seed()
        log_seed_status()

        # 2. Ingest
        logger.info("Phase 1: Data Ingestion...")
        ingest_main()

        # 3. Clean
        logger.info("Phase 2: Data Cleaning...")
        clean_main()

        # 4. Model
        logger.info("Phase 3: Statistical Modeling...")
        model_main()

        # 5. Robustness
        logger.info("Phase 4: Robustness Check...")
        robustness_main()

        # 6. Visualization & Report
        logger.info("Phase 5: Visualization & Reporting...")
        viz_main()
        report_main()

        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")
        logger.info("Check 'outputs/' for results.")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())