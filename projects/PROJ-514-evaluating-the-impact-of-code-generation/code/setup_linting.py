"""
Script to verify and ensure linting configuration is correct.
This script is a placeholder for verification purposes; the actual configuration
is defined in pyproject.toml.
"""
import os
import sys
import subprocess
from pathlib import Path
import logging
from utils.logger import get_logger

def ensure_requirements():
    """Ensure ruff and black are installed."""
    logger = get_logger(__name__)
    try:
        import ruff
        import black
        logger.info("Linting tools (ruff, black) are available.")
        return True
    except ImportError:
        logger.error("Linting tools not found. Please run: pip install -e .[dev]")
        return False

def create_ruff_config():
    """
    Verify ruff configuration exists in pyproject.toml.
    Since we use pyproject.toml, this function checks its presence.
    """
    logger = get_logger(__name__)
    root = Path(__file__).parent.parent
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        logger.error("pyproject.toml not found at project root.")
        return False
    
    content = pyproject.read_text()
    if "[tool.ruff]" not in content:
        logger.error("[tool.ruff] section missing in pyproject.toml.")
        return False
    
    logger.info("Ruff configuration found in pyproject.toml.")
    return True

def create_black_config():
    """
    Verify black configuration exists in pyproject.toml.
    Since we use pyproject.toml, this function checks its presence.
    """
    logger = get_logger(__name__)
    root = Path(__file__).parent.parent
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        logger.error("pyproject.toml not found at project root.")
        return False
    
    content = pyproject.read_text()
    if "[tool.black]" not in content:
        logger.error("[tool.black] section missing in pyproject.toml.")
        return False
    
    logger.info("Black configuration found in pyproject.toml.")
    return True

def main():
    """Main entry point for linting setup verification."""
    logger = get_logger(__name__)
    logger.info("Verifying linting configuration...")
    
    if not ensure_requirements():
        sys.exit(1)
    
    if not create_ruff_config():
        sys.exit(1)
    
    if not create_black_config():
        sys.exit(1)
    
    logger.info("Linting configuration verified successfully.")
    logger.info("Run 'ruff check .' to check for linting errors.")
    logger.info("Run 'black --check .' to check formatting.")

if __name__ == "__main__":
    main()