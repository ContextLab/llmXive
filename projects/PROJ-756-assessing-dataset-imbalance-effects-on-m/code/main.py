import os
import sys
import logging
from pathlib import Path
from setup_structure import create_directories

def run_pipeline(args=None):
    """
    Main entry point for the pipeline.
    Initializes structure and runs core tasks.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/pipeline.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    logger.info("Initializing project structure...")
    create_directories()

    logger.info("Project structure ready. Pipeline entry point reached.")
    logger.info("Run specific tasks via: python code/<task>.py")
    
    if args and args == "--full-pipeline":
        logger.info("Full pipeline flag detected. Executing sequence...")
        # Placeholder for full sequence execution
        # In a real run, this would chain: ingestion -> descriptors -> training -> evaluation
        logger.info("Full pipeline execution placeholder. See tasks.md for sequence.")

    return 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-pipeline", action="store_true")
    args = parser.parse_args()
    sys.exit(run_pipeline(args))