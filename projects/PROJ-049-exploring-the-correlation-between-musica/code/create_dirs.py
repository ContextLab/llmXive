import seed
"""
Directory creation helper.

This script provides a simple entry point that ensures the required
project directories exist. It imports ``seed`` as the very first line
to satisfy the deterministic‑seed requirement for all pipeline scripts.
"""

import sys
from pathlib import Path
import logging

from setup_directories import create_directory_structure

logger = logging.getLogger(__name__)

def main() -> int:
    """
    Create the required directory structure.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    try:
        create_directory_structure()
        logger.info("Directory structure created successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to create directory structure: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
