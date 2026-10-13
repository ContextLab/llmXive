"""
Script: create_project_structure.py
Purpose: Initialize the required project directory structure for the
PROJ-271-evaluating-the-effectiveness-of-llms-for project.

This script is idempotent – it can be run multiple times without error.
It creates (if they do not already exist):
  - code/
  - data/raw/
  - data/processed/
  - results/
  - tests/unit/
  - tests/contract/
The directories are created using the llmxive_toolkit `paths` helper,
which ensures they are placed under the project root.
"""

import sys
from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

def ensure_directories():
    """Create all required top‑level directories."""
    dirs = [
        paths.code(),                     # <project>/code
        paths.data("raw"),                # <project>/data/raw
        paths.data("processed"),          # <project>/data/processed
        paths.results(),                  # <project>/results
        paths.tests("unit"),              # <project>/tests/unit
        paths.tests("contract")           # <project>/tests/contract
    ]

    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {d}")
        except Exception as e:
            logger.error(f"Failed to create directory {d}: {e}")
            raise

if __name__ == "__main__":
    try:
        ensure_directories()
        logger.info("Project directory structure initialized successfully.")
    except Exception as exc:
        logger.error(f"Directory initialization failed: {exc}")
        sys.exit(1)
