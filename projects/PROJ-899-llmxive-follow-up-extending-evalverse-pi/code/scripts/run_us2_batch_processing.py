"""
Script to run T022: Batch processing logic for US2 timing profiling.

This script invokes the batch processing pipeline and writes
data/processed/batch_stats.json as required by T022.
"""
import os
import sys
import logging
from pathlib import Path

# Add code directory to path
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from src.cli.run_pipeline import main as batch_processing_main
from src.utils import setup_logging

def main():
    """Entry point for running batch processing."""
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Running T022: Batch processing logic")
    
    try:
        result = batch_processing_main()
        if result == 0:
            logger.info("T022 completed successfully")
        else:
            logger.error(f"T022 failed with exit code {result}")
            sys.exit(result)
    except Exception as e:
        logger.error(f"T022 failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()