import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.data.acquisition import main as run_interpolation_validation
from src.utils.logging import setup_logger

def main():
    logger = setup_logger(__name__)
    logger.info("Starting T015e: Interpolation Validation")
    
    try:
        result = run_interpolation_validation()
        logger.info(f"T015e completed successfully. Result: {result}")
        return 0
    except Exception as e:
        logger.error(f"T015e failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
