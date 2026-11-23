import os
import sys
import logging
from pathlib import Path

# Add code directory to path
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from src.models.metrics import main
from src.utils import setup_logging

def main_wrapper():
    """
    Wrapper script to run the permutation test (T020a).
    """
    setup_logging()
    logger = logging.getLogger("run_permutation_test")
    
    try:
        logger.info("Executing permutation test pipeline (T020a)")
        result = main()
        logger.info("Permutation test completed successfully")
        return result
    except Exception as e:
        logger.error(f"Permutation test failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main_wrapper())