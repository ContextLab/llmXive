import os
import sys
from pathlib import Path

from utils.logging_config import get_logger
from code.setup_directories import main as setup_dirs_main

def main():
    """
    Main entry point for the pipeline.
    Currently orchestrates the initial directory setup.
    """
    logger = get_logger("main")
    logger.info("Starting llmXive pipeline execution...")
    
    # Step 1: Ensure project structure exists
    try:
        setup_dirs_main()
    except Exception as e:
        logger.error(f"Failed to setup directories: {e}")
        sys.exit(1)
    
    logger.info("Pipeline initialization complete.")
    # Future steps would be called here (e.g., data ingestion, analysis)

if __name__ == "__main__":
    main()