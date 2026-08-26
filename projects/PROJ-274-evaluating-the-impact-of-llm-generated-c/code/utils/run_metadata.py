"""
Run Metadata Initialization Module (Task T010b)

Generates and manages run metadata including RUN_ID (UUID), start_time,
and project_version. Ensures the state directory exists and writes
the metadata to state/run_metadata.json.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add parent directory to path to allow imports if run as script
if __name__ == "__main__":
    parent_dir = Path(__file__).resolve().parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

from utils.seed import set_global_seed

def ensure_metadata_dir() -> Path:
    """
    Ensures the 'state' directory exists within the project root.
    Returns the path to the state directory.
    """
    # Determine project root based on file location
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    state_dir = project_root / "state"
    
    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
    
    return state_dir

def generate_run_metadata() -> dict:
    """
    Generates a dictionary containing run metadata.
    
    Returns:
        dict: Contains RUN_ID, start_time, and project_version.
    """
    set_global_seed(42) # Enforce reproducibility per T004
    
    run_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc).isoformat()
    project_version = "1.0.0" # Default version, can be extended to read from git/plan
    
    return {
        "RUN_ID": run_id,
        "start_time": start_time,
        "project_version": project_version
    }

def save_metadata(metadata: dict, output_path: Path) -> None:
    """
    Saves the metadata dictionary to a JSON file.
    
    Args:
        metadata: The metadata dictionary to save.
        output_path: The path where the JSON file will be written.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

def load_metadata(input_path: Path) -> dict:
    """
    Loads metadata from a JSON file.
    
    Args:
        input_path: The path to the JSON file.
        
    Returns:
        dict: The loaded metadata.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """
    Main entry point to initialize run metadata.
    Writes state/run_metadata.json.
    """
    state_dir = ensure_metadata_dir()
    output_file = state_dir / "run_metadata.json"
    
    metadata = generate_run_metadata()
    save_metadata(metadata, output_file)
    
    print(f"Run metadata initialized successfully.")
    print(f"RUN_ID: {metadata['RUN_ID']}")
    print(f"Start Time: {metadata['start_time']}")
    print(f"Output written to: {output_file}")

if __name__ == "__main__":
    main()
