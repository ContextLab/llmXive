import os
import sys
import json
import logging
from pathlib import Path

# Import the main logic from validation.py
# Note: In a real package structure, we would use relative imports or proper package setup.
# Here we assume the script is run from the project root or code/ directory.
# We add the parent directory to path to allow importing validation.py
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from validation import main as run_rubric_selection_main

def main():
    """
    Wrapper script to execute T021d repository filtering logic.
    This script is invoked by the run-book/quickstart.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('run_rubric_selection')
    
    logger.info("Executing T021d: Repository Selection Rubric...")
    exit_code = run_rubric_selection_main()
    
    if exit_code == 0:
        logger.info("T021d completed successfully.")
    else:
        logger.error("T021d failed.")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())