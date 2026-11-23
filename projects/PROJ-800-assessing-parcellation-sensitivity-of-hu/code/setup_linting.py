"""
Script to initialize linting and formatting configuration.
This script ensures the necessary configuration files exist in the project root
and provides helper commands for running ruff and black.
"""
import os
import sys
from pathlib import Path

# Import existing logger utilities
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """
    Main entry point for setting up linting configuration.
    Verifies that pyproject.toml and .pre-commit-config.yaml exist.
    """
    project_root = Path(__file__).resolve().parent.parent
    logger.info(f"Project root detected at: {project_root}")

    # Check for pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        logger.error(
            "pyproject.toml not found. "
            "Please ensure the project is initialized with the correct configuration."
        )
        sys.exit(1)
    else:
        logger.info("pyproject.toml found.")

    # Check for .pre-commit-config.yaml
    pre_commit_path = project_root / ".pre-commit-config.yaml"
    if not pre_commit_path.exists():
        logger.warning(
            ".pre-commit-config.yaml not found. "
            "Pre-commit hooks will not be available until configured."
        )
    else:
        logger.info(".pre-commit-config.yaml found.")

    # Check for .ruff.toml (optional, usually extends pyproject.toml)
    ruff_config_path = project_root / ".ruff.toml"
    if ruff_config_path.exists():
        logger.info(".ruff.toml found.")

    logger.info("Linting configuration verification complete.")
    logger.info("To run checks manually:")
    logger.info("  ruff check .")
    logger.info("  ruff format .")
    logger.info("  black --check .")

if __name__ == "__main__":
    main()