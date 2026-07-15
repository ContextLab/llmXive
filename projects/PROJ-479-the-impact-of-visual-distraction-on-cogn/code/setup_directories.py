import os
import sys
import logging
from utils import get_logger

def ensure_dir(path: str) -> None:
    """Create directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        logger = get_logger(__name__)
        logger.info(f"Created directory: {path}")

def main():
    """Setup the required data and results directory structure."""
    logger = get_logger(__name__)
    logger.info("Starting directory setup for PROJ-479...")

    # Base directories (already created in T001, but ensuring existence)
    ensure_dir("data")
    ensure_dir("results")

    # Data subdirectories
    ensure_dir("data/raw")
    ensure_dir("data/processed")

    # Results subdirectories
    ensure_dir("results/statistics")
    ensure_dir("results/plots")
    ensure_dir("results/sensitivity")
    ensure_dir("results/methodology")

    logger.info("Directory structure setup complete.")

if __name__ == "__main__":
    main()