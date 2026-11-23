import os
import sys
from pathlib import Path
import argparse
import logging
from src.utils.logger import get_logger

def get_project_root() -> Path:
    """Determine the project root directory."""
    # Assume the project root is the parent of the 'code' directory
    # or the current working directory if 'code' is not found.
    current_path = Path(__file__).resolve()
    code_dir = current_path.parent
    # If 'code' is a subdirectory of the project root
    if code_dir.name == "code":
        return code_dir.parent
    return code_dir

def setup_directories() -> bool:
    """
    Create the required project directory structure.
    Returns True if all directories were created successfully or already exist.
    Returns False and logs an error if verification fails.
    """
    logger = get_logger("setup")
    root = get_project_root()

    # Define the required directory structure relative to the project root
    required_dirs = [
        "src",
        "src/ingestion",
        "src/preprocessing",
        "src/analysis",
        "src/utils",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "data/processed/results",
        "docs",
        "state",
    ]

    logger.info(f"Project root identified at: {root}")
    all_success = True

    for dir_name in required_dirs:
        dir_path = root / dir_name
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            else:
                logger.debug(f"Directory already exists: {dir_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            all_success = False

    # Verification step: Explicitly check if all directories exist
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = root / dir_name
        if not dir_path.is_dir():
            missing_dirs.append(str(dir_path))

    if missing_dirs:
        logger.error(f"Verification failed. Missing directories: {missing_dirs}")
        return False

    logger.info("Project directory structure setup and verified successfully.")
    return True

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Setup the project directory structure."
    )
    return parser

def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    success = setup_directories()
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
