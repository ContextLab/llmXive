"""
Script to run the Yukawa Potential Solver and generate validation data.
This script is the entry point for T002.
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from physics.yukawa_solver import main as yukawa_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Executing Yukawa Potential Solver Validation (T002).")
    try:
        S = yukawa_main()
        logger.info(f"Validation successful. Sommerfeld Factor S = {S:.4f}")
        return 0
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())