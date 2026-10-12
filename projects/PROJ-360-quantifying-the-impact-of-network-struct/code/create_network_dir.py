"""
create_network_dir.py - Ensure the processed networks directory exists.

This script creates the directory `data/processed/networks/` using the
project's path utilities. It can be run as part of the setup phase
before any network construction steps.
"""

import logging
from llmxive_toolkit import paths

def setup_logger() -> logging.Logger:
    """Configure a simple logger for this script."""
    logger = logging.getLogger("create_network_dir")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def main() -> None:
    """
    Main entry point.

    Creates the `data/processed/networks/` directory (including any missing
    parent directories) and logs the action.
    """
    logger = setup_logger()
    # The `paths.data` helper creates the directory if it does not exist.
    network_dir = paths.data("processed", "networks")
    logger.info(f"Ensured existence of directory: {network_dir}")

if __name__ == "__main__":
    main()