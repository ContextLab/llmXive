"""
Finalize Research: Run hash_artifacts.py to finalize state/ and mark research complete.

This script serves as the entry point for T040. It invokes the hash_artifacts utility
to compute SHA256 hashes for all code and data artifacts, updates the state/ JSON file,
and logs the completion of the research pipeline.

This implements the 'Constitution Principle V' by ensuring all artifacts are hashed
and the state is finalized before marking the research as complete.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import init_pipeline_logging, get_logger
from utils.hash_artifacts import main as hash_main

def main():
    """
    Main entry point for finalizing the research pipeline.
    
    1. Initialize logging
    2. Run the hash_artifacts script to compute hashes and update state/
    3. Log completion
    """
    # Initialize logging
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    logger = init_pipeline_logging(
        name="finalize_research",
        log_file=log_dir / "finalize_research.log",
        level=logging.INFO
    )
    
    logger.info("Starting research finalization (T040)...")
    logger.info("This will run hash_artifacts.py to compute hashes and finalize state/")
    
    try:
        # Run the hash_artifacts main function
        # This will compute hashes for code/ and data/ directories
        # and update state/ directory with the results
        logger.info("Executing hash_artifacts.py...")
        hash_main()
        
        logger.info("Hash artifacts computation completed successfully.")
        logger.info("State directory has been updated with artifact hashes.")
        logger.info("Research pipeline T040 completed successfully.")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during research finalization: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())