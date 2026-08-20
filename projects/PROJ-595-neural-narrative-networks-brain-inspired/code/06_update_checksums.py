"""
Task T022: Run utils/checksums.py after data processing and update state file.

This script computes checksums for all files in the data/processed and data/text
directories and updates the state file to record the chain of custody.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.checksums import compute_directory_checksums, update_state_file, load_state_file
from utils.logging_config import get_logger, info, error, warning
from config import get_config

def main():
    """
    Main entry point for T022: Update checksums after data processing.
    """
    # Initialize logger
    logger = get_logger()
    info("T022: Starting checksum update for processed data...")
    
    # Load configuration
    config = get_config()
    project_root = Path(__file__).parent.parent
    data_processed_dir = project_root / "data" / "processed"
    data_text_dir = project_root / "data" / "text"
    state_file_path = project_root / "state" / "pipeline_state.json"
    
    # Ensure directories exist
    if not data_processed_dir.exists():
        error(f"T022: Data processed directory does not exist: {data_processed_dir}")
        sys.exit(1)
    
    if not state_file_path.parent.exists():
        error(f"T022: State directory does not exist: {state_file_path.parent}")
        sys.exit(1)
    
    # Compute checksums for processed data
    info(f"T022: Computing checksums for {data_processed_dir}")
    processed_checksums = compute_directory_checksums(data_processed_dir)
    info(f"T022: Found {len(processed_checksums)} files in processed data")
    
    # Compute checksums for text data if directory exists
    text_checksums = {}
    if data_text_dir.exists():
        info(f"T022: Computing checksums for {data_text_dir}")
        text_checksums = compute_directory_checksums(data_text_dir)
        info(f"T022: Found {len(text_checksums)} files in text data")
    
    # Load current state
    current_state = load_state_file(state_file_path)
    
    # Update state with new checksums
    update_state_file(
        state_file_path,
        {
            "processed_data": processed_checksums,
            "text_data": text_checksums,
            "update_timestamp": current_state.get("last_update", None),
            "task_id": "T022"
        }
    )
    
    info("T022: Checksum update completed successfully")
    info(f"T022: State file updated at {state_file_path}")
    
    # Log summary
    info(f"T022: Processed files checksums: {len(processed_checksums)}")
    info(f"T022: Text files checksums: {len(text_checksums)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())