"""
Main setup script to initialize the project directory structure.
This script orchestrates the creation of all required directories
including code, tests, data (raw/processed), and results.
"""
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    PROJECT_ROOT, CODE_DIR, DATA_DIR, DATA_RAW_DIR, 
    DATA_PROCESSED_DIR, RESULTS_DIR, FIGURES_DIR, 
    TESTS_DIR, LOG_DIR
)
from utils.logger import get_logger

logger = get_logger(__name__)

def ensure_dir(directory_path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not directory_path.exists():
        directory_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory_path}")
    else:
        logger.debug(f"Directory already exists: {directory_path}")

def main() -> int:
    """Execute the setup of the project structure."""
    logger.info("Initializing project directory structure...")
    
    # Define all directories to ensure
    directories = [
        PROJECT_ROOT,
        CODE_DIR,
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        RESULTS_DIR,
        FIGURES_DIR,
        TESTS_DIR,
        LOG_DIR,
        # Subdirectories for organization
        CODE_DIR / "models",
        CODE_DIR / "metrics",
        CODE_DIR / "calibration",
        CODE_DIR / "evaluation",
        CODE_DIR / "scripts",
        CODE_DIR / "utils",
        TESTS_DIR / "unit",
        TESTS_DIR / "integration",
        TESTS_DIR / "contract",
    ]

    for dir_path in directories:
        ensure_dir(dir_path)

    logger.info("Project directory structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())