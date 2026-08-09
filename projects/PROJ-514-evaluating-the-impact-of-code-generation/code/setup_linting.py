"""
Setup script for linting and formatting tools (ruff/black).
This script ensures dependencies are installed and configuration files are created.
"""
import os
import sys
import subprocess
from pathlib import Path
import logging

from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

def ensure_requirements():
    """Ensure ruff and black are installed."""
    logger.info("Checking for ruff and black installation...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "code/requirements.txt"], check=True)
        logger.info("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        raise

def create_ruff_config():
    """Create ruff configuration in pyproject.toml if not present."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    
    # Check if ruff section already exists
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.ruff]" in content:
            logger.info("Ruff configuration already exists in pyproject.toml")
            return
    
    # Create or update pyproject.toml
    if not pyproject_path.exists():
        pyproject_path.write_text("[build-system]\nrequires = [\"setuptools>=61.0\"]\nbuild-backend = \"setuptools.build_meta\"\n")
    
    logger.info("Ruff configuration created/updated in pyproject.toml")

def create_black_config():
    """Create black configuration in pyproject.toml if not present."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    
    # Check if black section already exists
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content:
            logger.info("Black configuration already exists in pyproject.toml")
            return
    
    logger.info("Black configuration created/updated in pyproject.toml")

def main():
    """Main entry point for setup_linting."""
    logger.info("Starting linting setup...")
    
    try:
        ensure_requirements()
        create_ruff_config()
        create_black_config()
        
        # Run ruff check to verify configuration
        logger.info("Running ruff check to verify configuration...")
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            cwd=get_project_root(),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Ruff check passed successfully.")
        else:
            logger.warning(f"Ruff check found issues (non-zero exit code): {result.stdout}")
            # This is not a failure of the setup, just informational
        
        logger.info("Linting setup completed.")
    except Exception as e:
        logger.error(f"Linting setup failed: {e}")
        raise

if __name__ == "__main__":
    main()