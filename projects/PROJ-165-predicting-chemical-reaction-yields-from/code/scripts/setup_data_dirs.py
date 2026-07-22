"""
Script to create the required data directory structure and initialize checksum logging.

This script:
1. Creates `data/raw/`, `data/processed/`, `data/artifacts/` directories.
2. Initializes `state/data_checksums.json` if it doesn't exist.
3. Logs the creation of directories and the initial state file.

Usage:
    python code/scripts/setup_data_dirs.py
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Define project root relative to this script location
    # Assuming script is at code/scripts/setup_data_dirs.py
    # Project root is code/../
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    artifacts_dir = data_dir / "artifacts"
    state_dir = project_root / "state"
    checksum_file = state_dir / "data_checksums.json"

    # Create directories
    directories = [data_dir, raw_dir, processed_dir, artifacts_dir, state_dir]
    
    logger.info(f"Project root identified as: {project_root}")
    
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.info(f"Directory already exists: {dir_path}")

    # Initialize checksum file if it doesn't exist
    if not checksum_file.exists():
        initial_state = {
            "created_at": datetime.utcnow().isoformat(),
            "checksums": {},
            "last_updated": datetime.utcnow().isoformat()
        }
        with open(checksum_file, 'w') as f:
            json.dump(initial_state, f, indent=2)
        logger.info(f"Initialized checksum file: {checksum_file}")
    else:
        logger.info(f"Checksum file already exists: {checksum_file}")

    logger.info("Data directory structure setup complete.")

if __name__ == "__main__":
    main()
