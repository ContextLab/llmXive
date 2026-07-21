"""
Runner script for T018: Filter species with <5 valid recordings per location.

This script executes the species filtering logic implemented in src/data/preprocessing.py
and generates the required output files for the audit trail.

Usage:
    python run_t018_species_filter.py
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data.preprocessing import main as run_species_filter
from src.utils.logging import setup_logger

def main():
    logger = setup_logger("run_t018")
    logger.info("Starting T018 species filter execution...")
    
    try:
        exit_code = run_species_filter()
        if exit_code == 0:
            logger.info("T018 species filter completed successfully.")
        else:
            logger.error(f"T018 species filter failed with exit code {exit_code}")
        return exit_code
    except Exception as e:
        logger.error(f"Unexpected error in T018 execution: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
