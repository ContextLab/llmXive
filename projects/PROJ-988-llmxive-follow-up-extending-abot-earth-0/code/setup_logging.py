"""
Setup script to initialize logging infrastructure.
This script ensures the logging configuration is applied at the start of the pipeline.
"""
import os
import sys
from pathlib import Path

# Add the code directory to the path to allow relative imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from lib.logging_config import setup_logging, get_logger

def main():
    """Initialize logging and verify the setup."""
    logger = get_logger("setup_logging")
    
    try:
        setup_logging()
        logger.info("Logging infrastructure configured successfully.", status="initialized")
        logger.info("Log file location: data/results/execution.log")
        return 0
    except Exception as e:
        logger.error(f"Failed to configure logging: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
