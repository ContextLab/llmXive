"""
Setup script to create the results directory structure.
This ensures that `results/` and `figures/` directories exist
before any evaluation scripts attempt to write output files.
"""
import os
from pathlib import Path
import sys

# Add parent directory to path to allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import PROJECT_ROOT, RESULTS_DIR, FIGURES_DIR
from utils.logger import get_logger

logger = get_logger(__name__)


def ensure_dir(directory_path: Path) -> None:
    """
    Ensure a directory exists. If not, create it and its parents.

    Args:
        directory_path: Path object representing the directory to create.
    """
    if not directory_path.exists():
        directory_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory_path}")
    else:
        logger.debug(f"Directory already exists: {directory_path}")


def main() -> int:
    """
    Main entry point for setting up results directories.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    logger.info("Starting results directory setup...")

    try:
        # Ensure results directory exists
        ensure_dir(RESULTS_DIR)

        # Ensure figures directory exists (often used alongside results)
        ensure_dir(FIGURES_DIR)

        # List created directories for verification
        logger.info(f"Results directory ready: {RESULTS_DIR}")
        logger.info(f"Figures directory ready: {FIGURES_DIR}")

        # Verify subdirectories expected by the pipeline
        expected_subdirs = ["coverage", "distributional", "significance", "conformal"]
        for subdir_name in expected_subdirs:
            subdir_path = RESULTS_DIR / subdir_name
            ensure_dir(subdir_path)
            logger.debug(f"Ensured subdirectory: {subdir_path}")

        logger.info("Results directory structure setup complete.")
        return 0

    except Exception as e:
        logger.error(f"Failed to setup results directories: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
