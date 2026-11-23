"""
Configuration script to ensure linting (ruff) and formatting (black) tools
are properly set up for the project.

This script verifies the presence of configuration files and can be used
to initialize them if missing.
"""
import os
import sys
from pathlib import Path
import logging
from config import get_logger, setup_logging

def check_config_file(file_path: Path, description: str) -> bool:
    """Check if a configuration file exists and is non-empty."""
    if not file_path.exists():
        logging.warning(f"{description} not found at {file_path}")
        return False
    
    if file_path.stat().st_size == 0:
        logging.warning(f"{description} at {file_path} is empty")
        return False
    
    logging.info(f"{description} found and valid at {file_path}")
    return True

def main():
    setup_logging()
    logger = get_logger(__name__)
    
    project_root = Path(__file__).parent.parent
    
    # Check for configuration files
    ruff_config = project_root / ".ruff.toml"
    black_config = project_root / "pyproject.toml"
    
    logger.info("Checking linting and formatting configuration...")
    
    ruff_ok = check_config_file(ruff_config, "Ruff configuration")
    black_ok = check_config_file(black_config, "Black configuration (in pyproject.toml)")
    
    if ruff_ok and black_ok:
        logger.info("Linting and formatting configuration is complete.")
        return 0
    else:
        logger.error("Some configuration files are missing or invalid.")
        return 1

if __name__ == "__main__":
    sys.exit(main())