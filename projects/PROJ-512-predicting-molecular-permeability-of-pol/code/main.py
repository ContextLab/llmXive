"""
Main entry point for the Molecular Permeability Prediction Pipeline.

This script initializes the environment, validates dependencies, and
provides a CLI for running pipeline stages.
"""
import os
import sys
import logging

# Ensure the project root is in the path
# When run as `python code/main.py`, the parent of 'code' is the project root
# We need to add the project root to sys.path to allow relative imports from sibling modules
# However, the task specifies imports like `from data.ingestion import ...`
# This implies the execution context should have `code/` as the root or we adjust path.
# Standard practice: run from project root as `python -m code.main` or adjust path here.

# Let's assume the script is run from the project root: `python -m code.main`
# OR we explicitly add the code directory to path if running as `python code/main.py`

def check_environment():
    """Verify required environment variables and dependencies."""
    logger = logging.getLogger(__name__)
    
    # Check for mandatory environment variables if any
    # Example: LOG_LEVEL
    log_level = os.getenv("MOL_PERM_LOG_LEVEL", "INFO")
    logger.info(f"Environment initialized with log level: {log_level}")

    # Verify critical imports
    try:
        import torch
        import rdkit
        import h5py
        logger.info("All critical dependencies (torch, rdkit, h5py) are available.")
    except ImportError as e:
        logger.error(f"Missing critical dependency: {e}")
        sys.exit(1)

    return True

def main():
    """Entry point for the pipeline."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if not check_environment():
        sys.exit(1)

    logger.info("Molecular Permeability Pipeline started.")
    
    # TODO: Add CLI argument parsing for stage selection (ingest, train, eval)
    # For now, this is the initialization shell.
    
    logger.info("Pipeline initialization complete.")

def setup_logging():
    """Basic logging setup if not already configured by utils."""
    log_level = os.getenv("MOL_PERM_LOG_LEVEL", "INFO").upper()
    log_level_val = getattr(logging, log_level, logging.INFO)
    
    logging.basicConfig(
        level=log_level_val,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

if __name__ == "__main__":
    main()
