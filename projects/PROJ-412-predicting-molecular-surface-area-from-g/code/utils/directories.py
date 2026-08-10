import os
import logging
from pathlib import Path
from typing import List

from .config import get_project_root
from .logging import get_logger

def create_all_directories() -> None:
    """
    Initialize the project directory structure for code, tests, results, and logs.
    Creates the following directories:
    - code/, code/data/, code/models/, code/eval/, code/utils/
    - tests/contract/, tests/unit/, tests/integration/
    - results/reports/, results/plots/, results/baseline/, results/predictions/
    - logs/
    """
    root = get_project_root()
    logger = get_logger("directories")

    # Define all required directories relative to project root
    dirs_to_create: List[Path] = [
        # Code structure
        root / "code",
        root / "code" / "data",
        root / "code" / "models",
        root / "code" / "eval",
        root / "code" / "utils",
        # Tests structure
        root / "tests" / "contract",
        root / "tests" / "unit",
        root / "tests" / "integration",
        # Results structure
        root / "results" / "reports",
        root / "results" / "plots",
        root / "results" / "baseline",
        root / "results" / "predictions",
        # Logs
        root / "logs",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")

    logger.info(f"Directory initialization complete. Created {created_count} new directories.")

def create_results_directories() -> None:
    """
    Specifically creates the results subdirectories.
    Used if only results structure needs to be initialized.
    """
    root = get_project_root()
    logger = get_logger("directories")

    results_dirs = [
        root / "results" / "reports",
        root / "results" / "plots",
        root / "results" / "baseline",
        root / "results" / "predictions",
    ]

    for dir_path in results_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created results directory: {dir_path}")

def main() -> None:
    """
    Entry point for running directory initialization as a script.
    """
    setup_logger = logging.getLogger("directories.main")
    setup_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    setup_logger.addHandler(handler)

    create_all_directories()
    setup_logger.info("Directory structure initialization finished.")

if __name__ == "__main__":
    main()
