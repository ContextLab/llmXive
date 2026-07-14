"""
T018: Run checksums after data processing and update state file.

This script computes SHA-256 checksums for all processed data artifacts
generated in User Story 1 and updates the project state file.
"""
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.checksums import compute_directory_checksums, update_state_file, load_state_file
from utils.logging_config import get_logger, info, error, warning
from config import get_config

def main():
    logger = get_logger("checksums")
    config = get_config()
    
    # Define the directories to checksum (processed data from US1)
    data_dirs = [
        project_root / "data" / "neural" / "processed",
        project_root / "data" / "text"
    ]
    
    # Filter to existing directories
    existing_dirs = [d for d in data_dirs if d.exists()]
    
    if not existing_dirs:
        error("No processed data directories found. Run data ingestion first.")
        return 1
    
    logger.info(f"Computing checksums for {len(existing_dirs)} directories")
    
    # Compute checksums for each directory
    all_checksums = {}
    for dir_path in existing_dirs:
        logger.info(f"Processing: {dir_path}")
        try:
            dir_checksums = compute_directory_checksums(dir_path)
            all_checksums[str(dir_path)] = dir_checksums
            info(f"  Found {len(dir_checksums)} files")
        except Exception as e:
            error(f"Failed to compute checksums for {dir_path}: {e}")
            return 1
    
    # Load existing state or create new
    state_file_path = project_root / "state" / "data_checksums.json"
    
    try:
        existing_state = load_state_file(state_file_path)
    except FileNotFoundError:
        existing_state = {}
        logger.info("Creating new state file")
    
    # Update state with new checksums
    updated_state = update_state_file(existing_state, all_checksums)
    
    # Save updated state
    try:
        update_state_file(updated_state, state_file_path, save=True)
        info(f"State file updated: {state_file_path}")
    except Exception as e:
        error(f"Failed to save state file: {e}")
        return 1
    
    logger.info("Checksum update complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
