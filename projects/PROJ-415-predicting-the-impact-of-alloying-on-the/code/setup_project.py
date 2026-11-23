import os
import sys
from pathlib import Path
from typing import List
from config import DATA_DIR, PROJECT_ROOT, LOG_DIR, ERRORS_DIR, MODELS_DIR, REPORTS_DIR
from utils.logging import get_logger

logger = get_logger(__name__)

def create_directories() -> None:
    """
    Create the core project directory structure:
    code/, tests/, data/, models/, reports/
    plus subdirectories for data (raw, curated, artifacts, logs) and errors.
    """
    # Core directories
    dirs: List[Path] = [
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "tests",
        DATA_DIR,
        MODELS_DIR,
        REPORTS_DIR,
        ERRORS_DIR,
        LOG_DIR,
        # Data subdirectories
        DATA_DIR / "raw",
        DATA_DIR / "curated",
        DATA_DIR / "artifacts",
        DATA_DIR / "logs",
    ]

    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {d}")
        else:
            logger.debug(f"Directory already exists: {d}")

def create_init_files() -> None:
    """
    Create __init__.py files in the new directories to make them packages.
    """
    init_paths: List[Path] = [
        PROJECT_ROOT / "code" / "__init__.py",
        PROJECT_ROOT / "tests" / "__init__.py",
        DATA_DIR / "__init__.py",
        MODELS_DIR / "__init__.py",
        REPORTS_DIR / "__init__.py",
        ERRORS_DIR / "__init__.py",
        LOG_DIR / "__init__.py",
        DATA_DIR / "raw" / "__init__.py",
        DATA_DIR / "curated" / "__init__.py",
        DATA_DIR / "artifacts" / "__init__.py",
        DATA_DIR / "logs" / "__init__.py",
    ]

    for p in init_paths:
        if not p.exists():
            p.touch()
            logger.debug(f"Created __init__.py: {p}")

def main() -> None:
    """
    Entry point to set up the project structure.
    """
    logger.info("Starting project structure setup...")
    create_directories()
    create_init_files()
    logger.info("Project structure setup complete.")

if __name__ == "__main__":
    main()
