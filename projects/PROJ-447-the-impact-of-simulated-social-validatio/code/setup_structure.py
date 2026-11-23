"""
Project structure setup module.

This module creates the required directory structure for the research pipeline.
"""

import os
import sys
from pathlib import Path
import logging

from utils.logger import get_logger

logger = get_logger(__name__)


def create_directories(base_path: Path) -> None:
    """
    Create the required directory structure.

    Args:
        base_path: Root path for the project.
    """
    directories = [
        "code", "code/data", "code/analysis", "code/viz", "code/utils",
        "data", "data/raw", "data/processed",
        "tests", "tests/unit", "tests/integration"
    ]

    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {full_path}")

    # Create __init__.py files
    for dir_path in directories:
        full_path = base_path / dir_path
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            logger.info(f"Created __init__.py in {full_path}")


def main() -> None:
    """
    Main entry point for structure setup.
    """
    logger.info("Executing main() for setup structure")

    # Determine base path (project root)
    base_path = Path(__file__).resolve().parent.parent

    create_directories(base_path)
    logger.info("Directory structure setup complete")


if __name__ == "__main__":
    main()
