"""
Task T001e: Create stimuli directory: `data/stimuli/`

This script ensures the existence of the `data/stimuli/` directory
required for storing experimental stimuli files (e.g., text prompts,
audio files, or images) used in the nostalgia vs control conditions.

It relies on the project's configuration and logging utilities.
"""
import os
import sys
import logging
from pathlib import Path

# Import from project API surface
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

STIMULI_DIR_NAME = "stimuli"
STIMULI_DIR_PATH = "data/stimuli"


def create_stimuli_directory() -> bool:
    """
    Creates the `data/stimuli/` directory if it does not exist.

    Returns:
        bool: True if the directory was created or already exists, False on failure.
    """
    config = get_config()
    project_root = config.get("project_root", ".")
    
    # Construct the full path relative to project root
    stimuli_path = Path(project_root) / STIMULI_DIR_PATH
    
    if stimuli_path.exists():
        if stimuli_path.is_dir():
            log_info(f"Stimuli directory already exists: {stimuli_path}")
            return True
        else:
            log_warning(f"Path exists but is not a directory: {stimuli_path}")
            return False

    try:
        # ensure_dirs handles the creation
        ensure_dirs([str(stimuli_path)])
        log_info(f"Successfully created stimuli directory: {stimuli_path}")
        return True
    except Exception as e:
        log_error(f"Failed to create stimuli directory {stimuli_path}: {e}")
        return False


def main() -> int:
    """
    Main entry point for T001e.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    # Setup logging
    log_level = get_config().get("log_level", logging.INFO)
    setup_logging(level=log_level, module_name="T001e")
    
    log_info("Starting Task T001e: Create stimuli directory")
    
    success = create_stimuli_directory()
    
    if success:
        log_info("Task T001e completed successfully.")
        return 0
    else:
        log_error("Task T001e failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())