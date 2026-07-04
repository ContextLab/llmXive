"""
Directory setup and initialization for the feature importance drift analysis pipeline.
"""
import os
import sys
from pathlib import Path

from utils.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


def ensure_directories() -> None:
    """
    Create all required directories for the pipeline.

    Creates:
        - data/raw/
        - data/processed/
        - outputs/
        - figures/
    """
    config = get_config()

    directories = [
        config.data_dir / "raw",
        config.data_dir / "processed",
        config.output_dir,
        config.output_dir.parent / "figures"
    ]

    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {dir_path}")

    logger.info("Directory structure initialized successfully")


def main() -> None:
    """Main entry point for setup_directories module."""
    ensure_directories()
    print("Directory structure created successfully.")


if __name__ == "__main__":
    main()
