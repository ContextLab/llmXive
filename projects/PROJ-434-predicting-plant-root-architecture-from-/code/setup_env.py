"""
Environment setup script for the plant root architecture prediction pipeline.

This script handles:
- Loading environment variables from .env file
- Setting up logging
- Validating required environment variables
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the code directory to the Python path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from utils.config import load_environment, get_env
from utils.logging_utils import setup_logging


def main():
    """Set up the environment for the pipeline."""
    # Initialize logging
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Starting environment setup...")

    # Load environment variables
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        logger.info(f"Loading environment variables from {env_path}")
        load_dotenv(env_path)
    else:
        logger.warning("No .env file found. Using system environment variables.")

    # Validate required environment variables
    required_vars = []  # Add any required variables here if needed
    missing_vars = [var for var in required_vars if not get_env(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    logger.info("Environment setup complete.")
    logger.info(f"Working directory: {Path.cwd()}")
    logger.info(f"Python version: {sys.version}")


if __name__ == "__main__":
    main()
