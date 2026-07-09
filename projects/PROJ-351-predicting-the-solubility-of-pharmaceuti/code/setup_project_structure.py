"""
Script to verify and document the project structure.
This script ensures that the required directories exist as per the implementation plan.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directory(path: Path) -> bool:
    """Create a directory if it does not exist."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    """
    Main entry point to create the project structure.
    Creates: code/, data/, models/, results/, tests/
    """
    root = Path.cwd()
    logger.info(f"Project root detected at: {root}")

    required_dirs = [
        "code",
        "data",
        "models",
        "results",
        "tests",
        "code/config",
        "code/data",
        "code/evaluation",
        "code/models",
        "code/training",
        "data/raw",
        "data/processed",
        "data/logs",
        "models/checkpoints",
        "results/plots",
        "results/tables",
        "tests/unit",
        "tests/integration"
    ]

    success = True
    for dir_path in required_dirs:
        full_path = root / dir_path
        if not create_directory(full_path):
            success = False

    if success:
        logger.info("Project structure verification complete. All directories present.")
        # List structure for verification
        for dir_path in required_dirs:
            full_path = root / dir_path
            if full_path.exists():
                print(f"[OK] {full_path}")
            else:
                print(f"[FAIL] {full_path}")
    else:
        logger.error("Project structure verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()