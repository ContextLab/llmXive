"""
Skeleton setup script (T000).

Creates the required directory hierarchy:
  - data/raw/
  - data/processed/
  - outputs/
  - tests/unit/
  - tests/integration/
  - tests/contract/

Writes a small ``README.txt`` file in each directory confirming creation.
"""

import sys
from pathlib import Path

try:
    from logging_config import get_logger
except ImportError:
    # Fallback if logging_config is not yet available in the environment
    import logging
    def get_logger(name):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(name)

logger = get_logger(__name__)

def _create_dir(path: Path) -> None:
    """Create a directory and a README.txt file inside it."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        readme = path / "README.txt"
        # Overwrite to ensure the file exists and is writable as per verification requirements
        readme.write_text(f"This directory ({path.name}) was created by the skeleton setup script.\n")
        logger.info(f"Created/verified directory and README at {path}")
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        raise

def main() -> int:
    """
    Execute the skeleton creation.
    Returns 0 on success, non‑zero on failure.
    """
    try:
        # Use the current working directory as the project root
        base = Path.cwd()
        
        # Required directory hierarchy
        dirs = [
            base / "data" / "raw",
            base / "data" / "processed",
            base / "outputs",
            base / "tests" / "unit",
            base / "tests" / "integration",
            base / "tests" / "contract",
        ]

        for d in dirs:
            _create_dir(d)

        logger.info("Skeleton directories created successfully.")
        return 0
    except Exception as exc:
        logger.error(f"Skeleton setup failed: {exc}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())