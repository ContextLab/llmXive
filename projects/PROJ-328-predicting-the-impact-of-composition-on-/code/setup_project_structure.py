"""
Project structure setup and verification.
Task T001: Initialize project directory structure.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger("setup_project_structure")


def setup_directories() -> None:
    """Create the required directory structure."""
    directories = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "data/config",
        "data/checksums",
        "code/ingestion",
        "code/features",
        "code/models",
        "code/evaluation",
        "code/visualization",
        "code/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "logs",
        "docs",
        "models",
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {full_path}")

    # Create __init__.py files in code directories
    code_dirs = [
        "code/ingestion",
        "code/features",
        "code/models",
        "code/evaluation",
        "code/visualization",
        "code/utils",
    ]

    for dir_path in code_dirs:
        init_file = project_root / dir_path / "__init__.py"
        if not init_file.exists():
          init_file.touch()
          logger.info(f"Created __init__.py: {init_file}")


def verify_directory_structure() -> bool:
    """Verify that all required directories exist."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "data/config",
        "code/ingestion",
        "code/features",
        "code/models",
        "code/evaluation",
        "code/visualization",
        "code/utils",
        "tests/contract",
        "tests/integration",
    ]

    all_exist = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            logger.error(f"Missing directory: {full_path}")
            all_exist = False
        else:
            logger.info(f"Verified directory: {full_path}")

    return all_exist


def main():
    """Main entry point for project structure setup."""
    logger.info("Setting up project directory structure...")
    setup_directories()

    if verify_directory_structure():
        logger.info("Task T001 completed successfully: All directories created and verified.")
        return 0
    else:
        logger.error("Task T001 failed: Some directories are missing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())