"""
Task T001c: Create data/results/ directory.

This script ensures the existence of the `data/results/` directory,
which is required for storing statistical reports, sensitivity analyses,
and other output artifacts.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def create_results_directory() -> bool:
    """
    Creates the `data/results/` directory if it does not exist.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    config = get_config()
    # Determine the base path for data directory
    # Assuming standard structure: project_root/data/
    data_base = project_root / "data"
    results_dir = data_base / "results"
    
    try:
        # Ensure parent directories exist first
        data_base.mkdir(parents=True, exist_ok=True)
        
        # Create the results directory
        results_dir.mkdir(parents=True, exist_ok=True)
        
        log_info(f"Successfully ensured existence of directory: {results_dir}")
        
        # Verify creation
        if not results_dir.exists():
            log_warning(f"Directory creation verification failed: {results_dir} does not exist.")
            return False
            
        if not results_dir.is_dir():
            log_warning(f"Path exists but is not a directory: {results_dir}")
            return False
            
        return True
        
    except PermissionError:
        log_error(f"Permission denied while creating directory: {results_dir}")
        return False
    except OSError as e:
        log_error(f"OS error while creating directory {results_dir}: {e}")
        return False
    except Exception as e:
        log_error(f"Unexpected error while creating directory {results_dir}: {e}")
        return False

def main():
    """Main entry point for the task."""
    # Setup logging
    log_level = logging.INFO
    setup_logging(level=log_level)
    
    log_info("Starting Task T001c: Create data/results/ directory")
    
    success = create_results_directory()
    
    if success:
        log_info("Task T001c completed successfully.")
        return 0
    else:
        log_error("Task T001c failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
