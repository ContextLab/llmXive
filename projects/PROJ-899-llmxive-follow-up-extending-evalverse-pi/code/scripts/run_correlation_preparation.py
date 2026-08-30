import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.metrics import main as metrics_main
from src.utils import setup_logging

def main():
    """Wrapper script for correlation data preparation."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Running correlation data preparation (T016a)...")
    
    exit_code = metrics_main()
    
    if exit_code == 0:
        logger.info("Correlation data preparation completed successfully.")
    else:
        logger.error("Correlation data preparation failed.")
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main())
