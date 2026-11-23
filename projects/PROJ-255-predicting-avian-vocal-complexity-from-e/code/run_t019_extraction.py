import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data.extraction import main
from src.utils.logging import setup_logger

def main_wrapper():
    """
    Wrapper for T019 extraction task execution.
    """
    # Setup logging
    logger = setup_logger('t019_extraction', 't019_extraction.log')
    
    logger.info("Starting T019: Vocal Metrics Extraction")
    
    # Run extraction
    result = main()
    
    if result == 0:
        logger.info("T019 completed successfully")
    else:
        logger.error(f"T019 failed with return code: {result}")
    
    return result

if __name__ == '__main__':
    sys.exit(main_wrapper())
