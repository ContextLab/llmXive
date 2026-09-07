"""
Setup script for linting and formatting tools.
This script ensures ruff and black are configured correctly and can be run.
"""
import subprocess
import sys
from pathlib import Path
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_tools():
    """Install linting and formatting tools if not present."""
    logger.info("Checking/Installing linting tools...")
    tools = [
        "ruff==0.0.287",
        "black==23.7.0",
        "pre-commit==3.4.0",
    ]
    for tool in tools:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", tool])
            logger.info(f"Installed {tool}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {tool}: {e}")
            raise

def create_ruff_config():
    """Ensure .ruff.toml exists (created by task T003 artifacts, this verifies it)."""
    ruff_config = Path(".ruff.toml")
    if not ruff_config.exists():
        logger.warning("Warning: .ruff.toml not found. Please ensure T003 artifacts are present.")
    else:
        logger.info("Found .ruff.toml configuration.")

def create_black_config():
    """Ensure pyproject.toml has black config (created by task T003 artifacts, this verifies it)."""
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        logger.warning("Warning: pyproject.toml not found. Please ensure T003 artifacts are present.")
    else:
        content = pyproject.read_text()
        if "[tool.black]" in content:
            logger.info("Found Black configuration in pyproject.toml.")
        else:
            logger.warning("Warning: Black configuration missing in pyproject.toml.")

def main():
    """Main entry point for setup."""
    logger.info("Starting linting and formatting setup...")
    try:
        install_tools()
        create_ruff_config()
        create_black_config()
        logger.info("Setup complete. Run 'ruff check .' and 'black --check .' to verify.")
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()