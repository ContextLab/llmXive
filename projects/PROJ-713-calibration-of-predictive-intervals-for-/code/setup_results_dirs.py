import os
from pathlib import Path
import sys
from config import PROJECT_ROOT, RESULTS_DIR, FIGURES_DIR
from utils.logger import get_logger

def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger = get_logger(__name__)
        logger.info(f"Created directory: {path}")
    else:
        logger = get_logger(__name__)
        logger.debug(f"Directory already exists: {path}")

def main() -> None:
    """Main entry point to ensure results directory structure exists."""
    logger = get_logger(__name__)
    logger.info("Initializing results directory structure...")

    # Ensure RESULTS_DIR exists
    ensure_dir(RESULTS_DIR)

    # Ensure FIGURES_DIR exists (subdirectory of results or project root as defined)
    ensure_dir(FIGURES_DIR)

    logger.info("Results directory structure initialized.")

if __name__ == "__main__":
    main()