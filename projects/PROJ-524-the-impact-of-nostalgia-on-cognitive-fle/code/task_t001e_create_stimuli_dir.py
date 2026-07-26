"""
Task T001e: Create stimuli directory.

This script creates the `data/stimuli/` directory required for storing
cognitive flexibility stimuli (e.g., WCST cards, nostalgia prompts).
It ensures the directory exists and is writable, logging the outcome.
"""
import os
import sys
import logging
from pathlib import Path

# Import project utilities and config
# Note: config.ensure_dirs is used to handle directory creation safely
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def create_stimuli_directory() -> bool:
    """
    Creates the stimuli directory at the configured path.

    Returns:
        bool: True if the directory was created or already exists, False on error.
    """
    config = get_config()
    if not config:
        log_warning("Configuration not loaded. Attempting to create default path.")
        stimuli_path = Path("data/stimuli")
    else:
        # Prefer config if available, otherwise default to data/stimuli
        stimuli_path = Path(config.get("paths", {}).get("stimuli", "data/stimuli"))

    try:
        # ensure_dirs handles creation and verification
        if ensure_dirs([str(stimuli_path)]):
            log_info(f"Stimuli directory created or verified: {stimuli_path.absolute()}")
            return True
        else:
            log_warning(f"Failed to create or verify stimuli directory: {stimuli_path}")
            return False
    except Exception as e:
        log_warning(f"Error creating stimuli directory: {e}")
        return False

def main():
    """Entry point for T001e execution."""
    # Setup logging
    logger = setup_logging()
    log_info("Starting T001e: Create stimuli directory")

    success = create_stimuli_directory()

    if success:
        log_info("T001e completed successfully.")
        sys.exit(0)
    else:
        log_warning("T001e failed to create stimuli directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()
