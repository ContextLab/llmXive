"""
Script to initialize the results directory structure for the project.
Creates the results/ directory and necessary subdirectories for storing
evaluation outputs, figures, and logs.
"""
import os
from pathlib import Path
import sys
from config import PROJECT_ROOT, RESULTS_DIR, FIGURES_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

def ensure_dir(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
    else:
        logger.debug(f"Directory already exists: {path}")

def main() -> None:
    """Create the results directory structure."""
    # Create the main results directory
    ensure_dir(RESULTS_DIR)

    # Create subdirectories for different types of results
    subdirs = [
        RESULTS_DIR / "coverage",
        RESULTS_DIR / "distributional_metrics",
        RESULTS_DIR / "significance_tests",
        RESULTS_DIR / "conformal_results",
        RESULTS_DIR / "benchmark",
        FIGURES_DIR,
    ]

    for subdir in subdirs:
        ensure_dir(subdir)

    logger.info("Results directory structure initialized successfully.")
    logger.info(f"Results root: {RESULTS_DIR}")
    logger.info(f"Figures root: {FIGURES_DIR}")

if __name__ == "__main__":
    main()
