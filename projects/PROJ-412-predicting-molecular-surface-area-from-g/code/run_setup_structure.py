import os
import sys
import logging
from pathlib import Path
from code.utils.logging import setup_logging, get_logger
from code.utils.directories import create_all_directories

def main():
    """
    Main entry point to create the project directory structure.
    This script satisfies T001a, T001b, T001c, and T001d by creating all required directories.
    """
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Executing directory structure setup (T001a-d)")

    # Create code structure (T001a)
    create_all_directories()

    # Create data structure (T001b)
    project_root = Path(__file__).parent.parent
    data_dirs = ["data/raw", "data/processed", "data/splits", "data/schemas"]
    for d in data_dirs:
        path = project_root / d
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created: {path}")

    # Create tests structure (T001c)
    test_dirs = ["tests/contract", "tests/unit", "tests/integration"]
    for d in test_dirs:
        path = project_root / d
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created: {path}")

    # Create results structure (T001d)
    results_dirs = ["results/reports", "results/plots"]
    for d in results_dirs:
        path = project_root / d
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created: {path}")

    logger.info("All directory structures created successfully.")

if __name__ == "__main__":
    main()
