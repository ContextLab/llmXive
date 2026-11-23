"""
Orchestrator script to fetch all required datasets.

This script calls fetch_assistments.py and fetch_khan_academy.py sequentially.
It handles the 300s timeout and error logging for both datasets.

Dependencies:
    - subprocess
    - sys
    - logging
"""

import subprocess
import sys
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/raw/fetch_datasets.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def fetch_assistments(timeout: int = 300) -> bool:
    """Fetch ASSISTments dataset."""
    logger.info("Starting fetch_assistments.py...")
    try:
        result = subprocess.run(
            [sys.executable, "code/download/fetch_assistments.py", "--timeout", str(timeout)],
            check=True,
            capture_output=False
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to fetch ASSISTments dataset: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error fetching ASSISTments: {e}")
        return False

def fetch_khan_academy(timeout: int = 300) -> bool:
    """Fetch Khan Academy dataset."""
    logger.info("Starting fetch_khan_academy.py...")
    try:
        result = subprocess.run(
            [sys.executable, "code/download/fetch_khan_academy.py", "--timeout", str(timeout)],
            check=True,
            capture_output=False
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to fetch Khan Academy dataset: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error fetching Khan Academy: {e}")
        return False

def main():
    """Main entry point."""
    logger.info("Starting fetch_datasets.py orchestrator.")
    
    success = True
    
    if not fetch_assistments():
        success = False
        logger.error("Pipeline aborted: ASSISTments fetch failed.")
    else:
        logger.info("ASSISTments fetch completed successfully.")
    
    if success and not fetch_khan_academy():
        success = False
        logger.error("Pipeline aborted: Khan Academy fetch failed.")
    elif success:
        logger.info("Khan Academy fetch completed successfully.")
    
    if success:
        logger.info("All datasets fetched successfully.")
        sys.exit(0)
    else:
        logger.error("One or more dataset fetches failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()