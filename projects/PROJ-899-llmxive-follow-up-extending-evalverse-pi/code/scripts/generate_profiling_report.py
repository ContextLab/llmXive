import os
import sys
import logging
from pathlib import Path

# Add code to path if not already
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.reports.generate import main as reports_main
from src.utils import setup_logging

def main():
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Executing T023: Generate Profiling Report Script")
    
    try:
        exit_code = reports_main()
        if exit_code == 0:
            logger.info("Profiling report generation succeeded.")
        else:
            logger.error("Profiling report generation failed.")
        return exit_code
    except Exception as e:
        logger.error(f"Script execution failed with exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())