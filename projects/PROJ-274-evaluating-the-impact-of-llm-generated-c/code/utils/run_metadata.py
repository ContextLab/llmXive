"""
Run Metadata Initialization Module.

Generates and manages run metadata for the experiment pipeline.
Creates state/run_metadata.json with RUN_ID, start_time, and project_version.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
import sys

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.setup_paths import ensure_project_dirs

def ensure_metadata_dir():
    """Ensure the state directory exists."""
    ensure_project_dirs()
    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir

def generate_run_metadata():
    """
    Generate a new run metadata dictionary.
    
    Returns:
        dict: Metadata containing RUN_ID (UUID), start_time (ISO8601), and project_version.
    """
    return {
        "RUN_ID": str(uuid.uuid4()),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "project_version": "1.0.0"  # Hardcoded version for this pilot phase
    }

def save_metadata(metadata, output_path=None):
    """
    Save metadata to a JSON file.
    
    Args:
        metadata (dict): The metadata dictionary to save.
        output_path (Path, optional): Path to the output file. Defaults to state/run_metadata.json.
    
    Returns:
        Path: The path to the saved file.
    """
    if output_path is None:
        state_dir = ensure_metadata_dir()
        output_path = state_dir / "run_metadata.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    return output_path

def load_metadata(input_path=None):
    """
    Load metadata from a JSON file.
    
    Args:
        input_path (Path, optional): Path to the input file. Defaults to state/run_metadata.json.
    
    Returns:
        dict: The loaded metadata dictionary.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if input_path is None:
        state_dir = project_root / "state"
        input_path = state_dir / "run_metadata.json"
    
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """
    Main entry point for generating and saving run metadata.
    
    This function ensures the state directory exists, generates new metadata,
    saves it to state/run_metadata.json, and prints the RUN_ID.
    """
    try:
        # Ensure directory exists
        state_dir = ensure_metadata_dir()
        
        # Generate metadata
        metadata = generate_run_metadata()
        
        # Save to file
        output_path = save_metadata(metadata)
        
        # Log success
        print(f"Run metadata generated successfully.")
        print(f"RUN_ID: {metadata['RUN_ID']}")
        print(f"Saved to: {output_path}")
        
        return 0
    except Exception as e:
        print(f"Error generating run metadata: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
