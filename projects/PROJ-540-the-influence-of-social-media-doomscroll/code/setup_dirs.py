"""
Directory setup script for the project.
"""
import os
import sys
from pathlib import Path
import logging

from config import load_config, ensure_directories

logger = logging.getLogger(__name__)

def create_directories() -> None:
    """Creates required directories."""
    config = load_config()
    ensure_directories(config)
    logger.info("Directories created successfully.")

def main():
    """Main entry point."""
    create_directories()

if __name__ == '__main__':
    main()
