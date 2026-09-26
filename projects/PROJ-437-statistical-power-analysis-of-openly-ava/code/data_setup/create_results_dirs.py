"""
Task T001d: Create directory `results/`, `results/paper/`.

This module provides the logic to initialize the results directory structure
required for the statistical power analysis project. It ensures that the
`results/` and `results/paper/` directories exist on the filesystem.
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_results_directories(base_path: Optional[Path] = None) -> Path:
    """
    Create the required results directory structure.

    Args:
        base_path: The root directory of the project. Defaults to the parent
                   of the module file's location (code/data_setup/..).

    Returns:
        The Path object pointing to the created `results` directory.

    Raises:
        OSError: If the directories cannot be created due to permissions or other IO errors.
    """
    if base_path is None:
        # Default to project root (parent of code/data_setup)
        base_path = Path(__file__).resolve().parent.parent.parent

    results_dir = base_path / "results"
    paper_dir = results_dir / "paper"

    logger.info(f"Ensuring results directory exists at: {results_dir}")
    results_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Ensuring results/paper directory exists at: {paper_dir}")
    paper_dir.mkdir(parents=True, exist_ok=True)

    # Verify creation
    if not results_dir.exists() or not paper_dir.exists():
        raise OSError(f"Failed to create required directories: {results_dir}, {paper_dir}")

    logger.info("Results directory structure created successfully.")
    return results_dir


def main():
    """
    Entry point for command-line execution.
    """
    logger.info("Starting T001d: Create results directories.")
    try:
        create_results_directories()
        logger.info("Task T001d completed successfully.")
    except Exception as e:
        logger.error(f"Task T001d failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
