import os
import json
import hashlib
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.checksum import compute_file_checksum
from utils.seeds import set_deterministic_seed

# Configure logger
logger = get_logger(__name__)

# Constants
PROJECT_ID = "PROJ-122-identifying-structure-property-relations"
STATE_FILE_NAME = f"{PROJECT_ID}.yaml"
RAW_DATA_DIR = "data/raw"
STATE_DIR = "state/projects"

def load_or_fetch_real_data() -> List[Dict[str, Any]]:
    """
    Loads real data from the raw directory if it exists, otherwise attempts to fetch it.
    Since T019a (Verification Gate) must pass before this runs, we assume data is available
    in data/raw/ or a fetchable URL is configured.
    
    For this implementation, we scan data/raw/ for CSV/JSON files.
    """
    raw_path = project_root / RAW_DATA_DIR
    if not raw_path.exists():
        logger.error(f"Raw data directory {raw_path} does not exist.")
        raise FileNotFoundError(f"Raw data directory {raw_path} not found. Run T019a verification first.")

    data_files = []
    for ext in ['*.csv', '*.json', '*.tsv']:
        data_files.extend(raw_path.glob(ext))

    if not data_files:
        logger.warning(f"No data files found in {raw_path}. Attempting to fetch from config...")
        # In a real scenario, this would trigger a fetch based on config.py URLs
        # For now, we fail loudly as per requirements
        raise FileNotFoundError("No data files found and fetch logic not triggered in this specific script context.")

    logger.info(f"Found {len(data_files)} data files in {raw_path}")
    return [str(f) for f in data_files]

def save_raw_data(data_files: List[str]) -> None:
    """
    Ensures data files are present in the raw directory.
    In a pipeline context, this might be a no-op if files are already downloaded,
    or it might move/copy them here.
    """
    logger.info("Ensuring raw data is saved to disk...")
    # Assuming files are already in data/raw from previous steps (T014-T018)
    # This function acts as a guard to ensure they are physically present.
    for f in data_files:
        if not os.path.exists(f):
            logger.error(f"Data file {f} missing from disk.")
            raise FileNotFoundError(f"Data file {f} not found on disk.")
    logger.info("Raw data verification complete.")

def compute_and_save_checksum(data_files: List[str], state_file_path: Path) -> Dict[str, str]:
    """
    Computes SHA-256 checksums for each raw data file and updates the project state file.
    """
    checksums = {}
    logger.info("Computing SHA-256 checksums for raw data files...")
    
    for file_path in data_files:
        path_obj = Path(file_path)
        if not path_obj.exists():
            logger.error(f"Cannot compute checksum for missing file: {file_path}")
            continue
        
        checksum = compute_file_checksum(path_obj)
        relative_path = str(path_obj.relative_to(project_root))
        checksums[relative_path] = checksum
        logger.info(f"Computed checksum for {relative_path}: {checksum[:16]}...")

    # Load existing state or create new
    state_dir = project_root / STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / STATE_FILE_NAME

    state_data = {}
    if state_file.exists():
        import yaml
        try:
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load existing state file: {e}. Creating new.")
    else:
        state_data = {
            "project_id": PROJECT_ID,
            "created_at": datetime.now().isoformat(),
            "artifacts": {}
        }

    # Update state with checksums
    if "artifacts" not in state_data:
        state_data["artifacts"] = {}
    
    state_data["artifacts"]["raw_data_checksums"] = checksums
    state_data["last_updated"] = datetime.now().isoformat()
    state_data["verification_status"] = "checksums_computed"

    # Write back to state file
    with open(state_file, 'w') as f:
        import yaml
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Project state updated at {state_file}")
    return checksums

def update_project_state(checksums: Dict[str, str]) -> None:
    """
    Wrapper to ensure state is updated.
    """
    state_file = project_root / STATE_DIR / STATE_FILE_NAME
    compute_and_save_checksum(list(checksums.keys()), state_file)

def main():
    """
    Main entry point for T020: Save raw data to data/raw/ with SHA-256 checksums.
    """
    logger.info("Starting T020: Save raw data and compute checksums.")
    
    # Set deterministic seed for any potential random operations (though checksums are deterministic)
    set_deterministic_seed(42)

    try:
        # 1. Load or fetch real data
        data_files = load_or_fetch_real_data()
        
        # 2. Save/Verify raw data exists on disk
        save_raw_data(data_files)
        
        # 3. Compute checksums and update state
        checksums = compute_and_save_checksum(data_files, project_root / STATE_DIR / STATE_FILE_NAME)
        
        logger.info("T020 completed successfully.")
        logger.info(f"Checksums computed for {len(checksums)} files.")
        
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during T020: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
