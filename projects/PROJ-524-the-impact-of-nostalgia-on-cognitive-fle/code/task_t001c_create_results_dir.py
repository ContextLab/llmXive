"""
Task T001c: Create the data/results/ directory.

This script ensures the existence of the 'data/results' directory,
which is required for storing statistical reports, sensitivity analyses,
and final output artifacts.
"""
import os
import sys
import logging
from pathlib import Path

from config import get_config, ensure_dirs
from utils import setup_logging, log_info


def create_results_directory():
    """
    Creates the data/results directory if it does not exist.

    Returns:
        Path: The path to the created/existing directory.
    """
    config = get_config()
    results_dir = Path(config.get("paths", {}).get("results", "data/results"))
    
    if not results_dir.exists():
        results_dir.mkdir(parents=True, exist_ok=True)
        log_info(f"Created directory: {results_dir}")
    else:
        log_info(f"Directory already exists: {results_dir}")
        
    return results_dir


def main():
    """
    Entry point for the task script.
    """
    setup_logging(level=logging.INFO)
    log_info("Starting task T001c: Create data/results directory")
    
    try:
        path = create_results_directory()
        log_info(f"Task T001c completed successfully. Path: {path}")
        return 0
    except Exception as e:
        log_error(f"Task T001c failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
