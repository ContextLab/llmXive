import os
import sys
import json
import logging
from pathlib import Path
from validation import main as run_rubric_main

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for T021a: Repository Selection Rubric Logic.
    This script executes the logic to generate data/raw/candidate_repos.json.
    """
    logger.info("Starting T021a: Repository Selection Rubric Logic")
    
    try:
        result = run_rubric_main()
        logger.info(f"T021a completed successfully. Output: data/raw/candidate_repos.json")
        return 0
    except Exception as e:
        logger.error(f"T021a failed with error: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
