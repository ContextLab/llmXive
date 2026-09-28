import os
import sys
import logging
from pathlib import Path

# Ensure the project root is in the path so we can import utils if needed
# though this script is self-contained.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_DIRS = [
    "code/data_ingestion",
    "code/modeling",
    "code/reporting",
    "code/utils",
    "tests",
    "data/raw",
    "data/processed",
    "results",
    "logs",
    "docs",
]

def ensure_directory(path: Path, logger: logging.Logger) -> bool:
    """
    Checks if a directory exists and is writable.
    Creates it if missing.
    Returns True if successful, False otherwise.
    """
    full_path = PROJECT_ROOT / path
    
    # Check existence
    if not full_path.exists():
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            return False
    
    # Check writability
    if not os.access(full_path, os.W_OK):
        logger.error(f"Directory {full_path} exists but is not writable.")
        return False
    
    return True

def main():
    """
    Verifies the project directory structure defined in tasks.md (Phase 1).
    Exits with code 0 if all directories are present and writable, 1 otherwise.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(PROJECT_ROOT / "logs" / "verify_directories.log")
        ]
    )
    logger = logging.getLogger(__name__)

    # Ensure logs dir exists first so we can write the log file
    logs_path = PROJECT_ROOT / "logs"
    if not logs_path.exists():
        logs_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info(f"Verifying directory structure...")

    all_ok = True
    for dir_path in REQUIRED_DIRS:
        if not ensure_directory(Path(dir_path), logger):
            all_ok = False

    if all_ok:
        logger.info("SUCCESS: All required directories exist and are writable.")
        sys.exit(0)
    else:
        logger.error("FAILURE: One or more directories are missing or not writable.")
        sys.exit(1)

if __name__ == "__main__":
    main()