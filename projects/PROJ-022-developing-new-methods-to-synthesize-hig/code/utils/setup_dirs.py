import os
import sys
from pathlib import Path
import logging
from utils.logging_config import setup_pipeline_logger

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    logging.debug(f"Ensured directory exists: {path}")

def setup_project_structure(root_path: Path) -> None:
    """
    Create the standard project directory structure.
    
    Creates:
    - code/
    - data/raw
    - data/processed
    - data/reports
    - tests/
    - artifacts/
    """
    logger = setup_pipeline_logger("setup_dirs")
    logger.info("Setting up project directory structure...")

    directories = [
        root_path / "code",
        root_path / "data" / "raw",
        root_path / "data" / "processed",
        root_path / "data" / "reports",
        root_path / "tests",
        root_path / "artifacts",
    ]

    for dir_path in directories:
        ensure_directory(dir_path)
        logger.info(f"Created/verified directory: {dir_path}")

    logger.info("Project directory structure setup complete.")

def main() -> None:
    """Entry point for CLI execution."""
    logger = setup_pipeline_logger("setup_dirs_main")
    root = Path.cwd()
    logger.info(f"Running setup from: {root}")
    setup_project_structure(root)
    logger.info("Setup complete.")

if __name__ == "__main__":
    main()
