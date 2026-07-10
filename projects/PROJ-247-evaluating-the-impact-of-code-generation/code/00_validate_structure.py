import os
import sys
from pathlib import Path
import logging
from datetime import datetime

# Base directory is the project root where this script is executed from
BASE_DIR = Path(__file__).resolve().parent.parent
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/ground_truth",
    "data/logs",
    "code/utils",
    "tests/unit",
    "tests/contract",
    "docs/paper",
    "scripts"
]

def setup_logging(log_path: Path) -> logging.Logger:
    """Configure logging to write to the structure validation log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path / "structure_validation.log"
    
    # Remove existing handlers to avoid duplicates if called multiple times
    logger = logging.getLogger("structure_validator")
    logger.handlers = []
    logger.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger

def validate_directory_structure(logger: logging.Logger, base_dir: Path, required_dirs: list) -> bool:
    """
    Check existence of all required directories relative to base_dir.
    Logs missing paths and returns True if all exist, False otherwise.
    """
    all_exist = True
    missing_dirs = []
    
    logger.info(f"Validating directory structure at: {base_dir}")
    logger.info(f"Checking {len(required_dirs)} required directories...")
    
    for rel_path in required_dirs:
        full_path = base_dir / rel_path
        if full_path.exists() and full_path.is_dir():
            logger.info(f"[OK] {rel_path}")
        else:
            logger.error(f"[MISSING] {rel_path}")
            missing_dirs.append(rel_path)
            all_exist = False
    
    if all_exist:
        logger.info("Validation PASSED: All required directories exist.")
    else:
        logger.error(f"Validation FAILED: {len(missing_dirs)} directories missing: {missing_dirs}")
    
    return all_exist

def main():
    """Entry point for directory structure validation."""
    log_dir = BASE_DIR / "data" / "logs"
    logger = setup_logging(log_dir)
    
    try:
        success = validate_directory_structure(logger, BASE_DIR, REQUIRED_DIRS)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"Unexpected error during validation: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
