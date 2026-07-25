"""
T004: Setup data directory structure.

Creates the required directory hierarchy for the project:
- data/raw/
- data/derived/
- data/processed/
- state/ (re-confirmed for checksums and logs)
- tests/ (re-confirmed for test artifacts)
- code/ (re-confirmed for source code)

This script ensures the directory tree exists on disk before any data
ingestion or processing tasks begin.
"""

import os
import sys
from pathlib import Path
import logging

# Configure basic logging for this script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("setup_data_structure")

def main():
    """Create the project directory structure."""
    # Define the project root (assuming this script is in code/, so root is parent)
    # However, standard practice in these pipelines is to run from root or pass root.
    # We will assume the script is run from the project root or determine it via __file__.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define the directories to create relative to project root
    directories = [
        "data/raw",
        "data/derived",
        "data/processed",
        "state",
        "tests",
        "code", # Ensure code exists even if we are inside it
        "figures", # Good practice for output figures
    ]

    created_count = 0
    existing_count = 0

    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
                created_count += 1
            except OSError as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
                sys.exit(1)
        else:
            logger.debug(f"Directory already exists: {dir_path}")
            existing_count += 1

    logger.info(f"Setup complete. Created: {created_count}, Existing: {existing_count}")
    
    # Verify the critical data paths specifically mentioned in T004
    critical_paths = [
        project_root / "data/raw",
        project_root / "data/derived",
        project_root / "data/processed"
    ]
    
    missing = [p for p in critical_paths if not p.exists()]
    if missing:
        logger.error(f"Critical directories are missing: {missing}")
        sys.exit(1)
        
    logger.info("All critical data directories verified.")

if __name__ == "__main__":
    main()