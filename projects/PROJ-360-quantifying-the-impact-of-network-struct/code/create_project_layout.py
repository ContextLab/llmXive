"""
create_project_layout.py - Ensure required top‑level project directories exist.

This script creates the following directories under the project root if they do not already exist:
  - data/processed/
  - models/
  - results/
  - code/

It uses the `llmxive_toolkit.paths` helpers which automatically create any missing parent
directories. The script is idempotent – running it multiple times will not raise errors.
"""

import sys
import logging
from llmxive_toolkit import paths, get_logger

# Configure a simple logger
log = get_logger(__name__)

def create_directories():
    """Create the required project‑level directories."""
    dirs = [
        paths.data("processed"),
        paths.models(),
        paths.results(),
        paths.code()
    ]

    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            log.info(f"Ensured directory exists: {d}")
        except Exception as e:
            log.error(f"Failed to create directory {d}: {e}")
            raise

def main():
    """Entry point for the script."""
    try:
        create_directories()
        print("Project layout directories created successfully.")
    except Exception as exc:
        print(f"Error creating project layout: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
