"""
Task T001e: Create stimuli directory: data/stimuli/

This script initializes the data/stimuli/ directory structure required for
storing nostalgia and control stimuli files. It ensures the directory exists
and creates a placeholder .gitkeep file to ensure the directory is tracked
in version control.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning, get_timestamp

def create_stimuli_directory():
    """
    Creates the data/stimuli/ directory and a .gitkeep placeholder file.
    
    Returns:
        bool: True if successful, False otherwise
    """
    config = get_config()
    base_dir = Path(config.get("paths", {}).get("data_dir", "data"))
    stimuli_dir = base_dir / "stimuli"
    
    try:
        # Create the directory if it doesn't exist
        stimuli_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep to ensure directory is tracked
        gitkeep_path = stimuli_dir / ".gitkeep"
        with open(gitkeep_path, "w") as f:
            f.write(f"# Stimuli directory for nostalgia cognitive flexibility study\n")
            f.write(f"# Created at: {get_timestamp()}\n")
            f.write(f"# This file ensures the directory exists in version control\n")
        
        log_info(f"Successfully created stimuli directory: {stimuli_dir}")
        log_info(f"Created placeholder file: {gitkeep_path}")
        
        return True
        
    except Exception as e:
        log_warning(f"Failed to create stimuli directory: {str(e)}")
        return False

def main():
    """Main entry point for T001e task."""
    # Setup logging
    log_level = get_config().get("logging", {}).get("level", "INFO")
    setup_logging(level=log_level)
    
    log_info("Starting task T001e: Create stimuli directory")
    
    success = create_stimuli_directory()
    
    if success:
        log_info("Task T001e completed successfully")
        return 0
    else:
        log_warning("Task T001e failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
