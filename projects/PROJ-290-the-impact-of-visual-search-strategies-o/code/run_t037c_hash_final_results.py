"""
Task T037c: Run hash_artifacts.py to update state/ with hashes after T026, T034 (Final Results).

This script executes the generic hash_artifacts utility to generate SHA-256 hashes
for all artifacts in `data/`, `code/`, and `results/`, updating `state/artifact_hashes.json`.
It ensures the final results (T026 sensitivity report, T034 results table) are checksummed.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.hash_artifacts import main as hash_main
from utils.logging import setup_logging, get_logger
from config import get_config

def main():
    """Entry point for T037c: Final Hash Update."""
    config = get_config()
    setup_logging(config)
    logger = get_logger("T037c")

    logger.info("Starting T037c: Updating artifact hashes for final results (T026, T034).")
    logger.info("Scanning directories: data/, code/, results/...")

    try:
        # Execute the generic hash_artifacts main function
        # This function is designed to scan the standard directories and write to state/
        hash_main()
        
        logger.info("T037c completed successfully. `state/artifact_hashes.json` updated.")
        return 0
    except Exception as e:
        logger.error(f"T037c failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
