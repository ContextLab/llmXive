"""
Run Metadata Management Module.
Handles initialization, generation, and persistence of run-specific metadata.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add project root to path for relative imports if run as script
project_root = Path(__file__).resolve().parents[2]
state_dir = project_root / "state"

def ensure_metadata_dir():
    """Ensure the state directory exists."""
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir

def generate_run_metadata():
    """
    Generate a new run metadata dictionary.
    Returns a dict with RUN_ID (UUID), start_time (ISO8601), and project_version.
    """
    return {
        "RUN_ID": str(uuid.uuid4()),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "project_version": "1.0.0"
    }

def save_metadata(metadata: dict, filename: str = "run_metadata.json"):
    """
    Save metadata dictionary to a JSON file in the state directory.
    """
    ensure_metadata_dir()
    file_path = state_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    return file_path

def load_metadata(filename: str = "run_metadata.json") -> dict:
    """
    Load metadata from a JSON file in the state directory.
    Returns None if file does not exist.
    """
    file_path = state_dir / filename
    if not file_path.exists():
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """
    CLI entry point to initialize run metadata.
    Generates and saves run_metadata.json.
    """
    print("Initializing run metadata...")
    metadata = generate_run_metadata()
    file_path = save_metadata(metadata)
    print(f"Run metadata saved to: {file_path}")
    print(f"RUN_ID: {metadata['RUN_ID']}")
    print(f"Start Time: {metadata['start_time']}")
    print(f"Project Version: {metadata['project_version']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
