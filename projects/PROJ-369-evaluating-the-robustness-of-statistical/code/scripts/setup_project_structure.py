"""
Script to explicitly create the required project directory structure.
This script ensures all necessary directories for the llmXive pipeline exist.
"""
import os
import sys
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_path, ensure_dirs
from src.utils.logging import setup_logger, log_info, log_error

REQUIRED_DIRECTORIES = [
    "src",
    "src/data",
    "src/synthesis",
    "src/analysis",
    "src/viz",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "data/raw",
    "data/processed",
    "data/results",
    "specs",
    "state"
]

def main():
    """Create the project directory structure."""
    logger = setup_logger("directory_setup")
    
    # Get project root using the config utility
    root = get_path("")
    logger.info(f"Creating project structure at: {root}")
    
    created_count = 0
    skipped_count = 0
    error_count = 0

    for dir_name in REQUIRED_DIRECTORIES:
        dir_path = root / dir_name
        try:
            if dir_path.exists():
                logger.debug(f"Directory exists: {dir_path}")
                skipped_count += 1
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
                created_count += 1
        except Exception as e:
            log_error(logger, f"Failed to create {dir_path}: {e}")
            error_count += 1

    log_info(logger, f"Directory setup complete. Created: {created_count}, Skipped: {skipped_count}, Errors: {error_count}")
    
    if error_count > 0:
        log_error(logger, "Some directories could not be created.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
