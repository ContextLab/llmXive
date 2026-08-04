import os
import sys
import logging
from pathlib import Path
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def create_stimuli_directory():
    """
    Creates the data/stimuli/ directory required for storing experimental stimuli.
    This is a foundational setup task (T001e).
    
    Returns:
        Path: The path to the created directory.
    
    Raises:
        OSError: If the directory cannot be created.
    """
    config = get_config()
    base_dir = config.get('base_dir', Path.cwd())
    stimuli_dir = base_dir / 'data' / 'stimuli'
    
    try:
        # ensure_dirs handles creation of parent directories if needed
        ensure_dirs(stimuli_dir)
        log_info(f"Stimuli directory created successfully: {stimuli_dir}")
        return stimuli_dir
    except OSError as e:
        log_error(f"Failed to create stimuli directory at {stimuli_dir}: {e}")
        raise

def main():
    """
    Entry point for the T001e task script.
    """
    # Setup logging
    log_level = get_config().get('log_level', 'INFO')
    setup_logging(level=log_level)
    
    log_info("Starting task T001e: Create stimuli directory")
    
    try:
        stimuli_path = create_stimuli_directory()
        log_info(f"Task T001e completed. Directory: {stimuli_path}")
        # Verify existence for robustness
        if not stimuli_path.exists():
            log_error("Verification failed: Directory does not exist after creation.")
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        log_error(f"Task T001e failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
