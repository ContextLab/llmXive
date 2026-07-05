import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.preprocessing import main

def main_wrapper():
    """Wrapper to run the sensitivity analysis task."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting T030a Sensitivity Execution")
    
    try:
        main()
        logger.info("T030a completed successfully")
    except Exception as e:
        logger.error(f"T030a failed: {e}")
        raise

if __name__ == "__main__":
    main_wrapper()
