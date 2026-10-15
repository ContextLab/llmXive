"""
Setup script for establishing the project layout.

This script is invoked via the quickstart guide:
    python code/setup_project.py

It creates the required directory structure under the project root:
- data/raw/
- data/processed/
- data/final/
- data/final/plots/
- code/
- tests/
- contracts/
- specs/
- logs/ (optional for runtime logging)

The actual directory creation logic lives in ``code/config.py`` under
:func:`ensure_directories`.  This wrapper provides a clean entry point
for users and integrates with the project's logging utilities.
"""
import sys
import logging
from config import ensure_directories, get_project_root
from utils import setup_logging, get_logger

def main() -> int:
    """
    Entry point for the setup script.

    Returns
    -------
    int
        Exit status code (0 for success, non‑zero for failure).
    """
    # Initialise logging (writes to stdout; optional file logging can be
    # configured via the project's ``utils`` module).
    setup_logging(level=logging.INFO)
    logger = get_logger(__name__)

    try:
        logger.info("Creating project layout...")
        ensure_directories()
        root = get_project_root()
        logger.info(f"Project layout successfully created under {root}")
        return 0
    except Exception as exc:  # pragma: no cover – unexpected failures are logged
        logger.error("Failed to create project layout", exc_info=exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())
