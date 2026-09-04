"""
Setup script to create the project directory structure.
Executes the creation of required directories for the metallic glass density prediction project.
"""
import os
from pathlib import Path
import logging

# Import logger from existing utility
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_directories() -> None:
    """
    Create the project directory structure as defined in the implementation plan.
    Directories created:
    - code/data, code/features, code/models, code/analysis
    - data, models, reports
    - tests/unit, tests/contract, tests/integration
    """
    # Determine project root: parent of code/
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code/data",
        "code/features",
        "code/models",
        "code/analysis",
        "data",
        "models",
        "reports",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "logs",
        "docs",
        "contracts",
        "state"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        except PermissionError:
            logger.error(f"Permission denied creating directory: {full_path}")
        except OSError as e:
            logger.error(f"Error creating directory {full_path}: {e}")

    logger.info(f"Project structure setup complete. Created {created_count} directories.")

def main() -> int:
    """
    Main entry point for the setup script.
    Returns 0 on success, 1 on failure.
    """
    try:
        setup_directories()
        return 0
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
