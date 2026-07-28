"""
Directory setup utilities for the project.

Creates the required directory structure for data, code, and state.
"""
import os
from pathlib import Path
from typing import List

from utils.logging import get_logger

logger = get_logger(__name__)


def create_directories(paths: List[Path]) -> None:
    """
    Create a list of directories, including parents if needed.

    Args:
        paths: List of directory paths to create
    """
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")


def ensure_data_structure() -> None:
    """
    Ensure the complete project directory structure exists.

    Creates:
    - data/raw, data/processed, data/results
    - state/projects
    - code/data, code/graph, code/stats, code/utils
    - tests/unit
    - docs
    """
    base_dir = Path(__file__).parent.parent

    directories = [
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "results",
        base_dir / "state" / "projects",
        base_dir / "code" / "data",
        base_dir / "code" / "graph",
        base_dir / "code" / "stats",
        base_dir / "code" / "utils",
        base_dir / "tests" / "unit",
        base_dir / "docs",
    ]

    create_directories(directories)
    logger.info("Project directory structure created")


def main() -> None:
    """Entry point for directory setup script."""
    ensure_data_structure()


if __name__ == "__main__":
    main()