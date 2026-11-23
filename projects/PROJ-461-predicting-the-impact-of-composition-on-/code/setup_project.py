import os
import logging
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_directories():
    """
    Create the project directory structure as per the implementation plan.
    Creates code/data, code/features, code/models, code/analysis, data, models,
    reports, logs, tests/unit, tests/contract, tests/integration.
    """
    base_path = Path(__file__).parent.parent
    
    directories = [
        base_path / "code" / "data",
        base_path / "code" / "features",
        base_path / "code" / "models",
        base_path / "code" / "analysis",
        base_path / "data",
        base_path / "models",
        base_path / "reports",
        base_path / "logs",
        base_path / "tests" / "unit",
        base_path / "tests" / "contract",
        base_path / "tests" / "integration",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")

    logger.info(f"Project structure setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for the setup script."""
    setup_directories()
    return 0

if __name__ == "__main__":
    exit(main())
