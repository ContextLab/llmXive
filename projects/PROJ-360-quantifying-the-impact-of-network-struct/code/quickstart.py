"""
Quickstart script to run the full pipeline up to T011.
This script orchestrates T008 (download), T009/T010/T011 (construct and save).
"""
import os
import sys
import time
import logging
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from download import main as download_main
from construct_network import main as construct_main
from utils import setup_logging

def main():
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Starting Quickstart Pipeline (T008 -> T011)")
    start_time = time.time()

    # Step 1: Download CIFs (T008)
    logger.info("Step 1: Downloading CIF files (T008)...")
    try:
        download_main()
    except Exception as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)

    # Step 2: Construct Networks and Save (T009, T010, T011)
    logger.info("Step 2: Constructing networks and saving (T009, T010, T011)...")
    try:
        construct_main()
    except Exception as e:
        logger.error(f"Construction failed: {e}")
        sys.exit(1)

    elapsed = time.time() - start_time
    logger.info(f"Quickstart pipeline completed in {elapsed:.2f} seconds.")
    logger.info("Check data/processed/networks/ and data/processed/network_manifest.json")

if __name__ == "__main__":
    main()