import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.extract_optical import main
from src.utils import setup_logging

def main_wrapper():
    """Wrapper to run the optical extraction main function."""
    logger = setup_logging("run_optical_extraction", level=logging.INFO)
    try:
        main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Optical extraction failed.")
            sys.exit(e.code)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main_wrapper()