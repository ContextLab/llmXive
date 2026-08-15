"""
T018: Run utils/checksums.py after data processing and update state file.

This script computes SHA-256 checksums for all processed data files in the
project's data directories and updates the state file to track data integrity.
It is designed to be run after data ingestion and preprocessing steps to
ensure data consistency and detect any corruption.

Output:
    Updates state/state.json with checksums for all tracked data files.
    Logs success or failure of the checksum update process.
"""
import os
import sys
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.checksums import compute_directory_checksums, update_state_file, load_state_file
from utils.logging_config import get_logger, info, error, warning
from config import get_config

def main():
    """
    Main entry point for T018: Update checksums after data processing.
    
    1. Loads configuration to determine data directories.
    2. Computes checksums for all files in the processed data directories.
    3. Updates the state file with the new checksums.
    4. Logs the result.
    """
    logger = get_logger("T018_checksums")
    info(logger, "Starting checksum update process for processed data.")
    
    config = get_config()
    data_root = Path("data")
    
    # Define directories to checksum based on US1 outputs
    # T013: data/neural/processed/roi_timecourses.csv
    # T017: data/neural/processed/event_averages.csv
    # T015: data/text/rocstories_sample.jsonl
    dirs_to_check = [
        data_root / "neural" / "processed",
        data_root / "text",
    ]
    
    # Filter to existing directories
    existing_dirs = [d for d in dirs_to_check if d.exists()]
    
    if not existing_dirs:
        error(logger, "No processed data directories found. Did you run T013, T015, and T017?")
        return 1
    
    info(logger, f"Found {len(existing_dirs)} data directory(ies) to checksum.")
    
    # Compute checksums for all files in these directories
    checksums = {}
    for d in existing_dirs:
        info(logger, f"Computing checksums for: {d}")
        dir_checksums = compute_directory_checksums(d)
        checksums.update(dir_checksums)
    
    if not checksums:
        error(logger, "No files found to checksum in the specified directories.")
        return 1
    
    info(logger, f"Computed checksums for {len(checksums)} file(s).")
    
    # Update the state file
    state_file_path = Path("state") / "state.json"
    try:
        update_state_file(state_file_path, checksums)
        info(logger, f"Successfully updated state file: {state_file_path}")
        return 0
    except Exception as e:
        error(logger, f"Failed to update state file: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())