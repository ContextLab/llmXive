"""
Directory Initialization Script for Crystal Structure Prediction Pipeline.

This script creates all required data directories for the project,
ensuring a consistent file structure for CPU-only execution.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List

# Add project root to path to import config if needed, though we use relative paths here
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Define all required directories relative to project root
REQUIRED_DIRS: List[Path] = [
    DATA_DIR / "raw",
    DATA_DIR / "processed",
    DATA_DIR / "results",
    DATA_DIR / "validation",
    DATA_DIR / "models",
    DATA_DIR / "processing",
    LOGS_DIR,
]

# Marker file to indicate initialization
INIT_MARKER = DATA_DIR / ".initialized"

def setup_logging() -> logging.Logger:
    """Configure basic logging for the initialization script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger("init_dirs")

def ensure_directory(dir_path: Path, logger: logging.Logger) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Path to the directory.
        logger: Logger instance.

    Returns:
        True if directory exists or was created, False otherwise.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ready: {dir_path}")
        return True
    except PermissionError as e:
        logger.error(f"Permission denied creating directory {dir_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating directory {dir_path}: {e}")
        return False

def write_initialization_log(logger: logging.Logger) -> bool:
    """
    Write a confirmation log to data/.initialized.

    Args:
        logger: Logger instance.

    Returns:
        True if successful, False otherwise.
    """
    try:
        marker_content = {
            "initialized_at": datetime.utcnow().isoformat(),
            "status": "success",
            "message": "All required directories created for CPU-only environment.",
            "note": "No CUDA-specific cache directories were created."
        }
        with open(INIT_MARKER, "w", encoding="utf-8") as f:
            json.dump(marker_content, f, indent=2)
        logger.info(f"Initialization marker written to: {INIT_MARKER}")
        return True
    except Exception as e:
        logger.error(f"Failed to write initialization marker: {e}")
        return False

def main() -> int:
    """
    Main entry point for directory initialization.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    logger = setup_logging()
    logger.info("Starting directory initialization for PROJ-030...")

    success = True
    for dir_path in REQUIRED_DIRS:
        if not ensure_directory(dir_path, logger):
            success = False

    if success:
        if write_initialization_log(logger):
            logger.info("Directory initialization completed successfully.")
            return 0
        else:
            logger.error("Directory initialization completed with errors writing marker.")
            return 1
    else:
        logger.error("Directory initialization failed due to directory creation errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
