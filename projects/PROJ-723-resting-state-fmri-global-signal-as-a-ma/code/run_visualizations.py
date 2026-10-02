"""
Runner script to execute the visualization generation pipeline (T035).

Usage:
    python code/run_visualizations.py
"""
import os
import sys
import logging
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from config import ensure_directories
from utils import get_logger
from visualizations import main

def main_entry():
    """Entry point for the visualization generation script."""
    logger = get_logger(__name__)
    logger.info("Starting visualization generation pipeline (T035)...")
    
    try:
        ensure_directories()
        main()
        logger.info("Visualization generation completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Visualization generation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main_entry())