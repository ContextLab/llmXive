"""
Task T004: Setup data directory structure and state tracking.

Creates the required directory hierarchy:
- data/raw/
- data/processed/
- data/logs/
- state/

Initializes the state tracking file (state/pipeline_state.json) if it does not exist.
"""
import os
import json
from pathlib import Path
from typing import List

# Project root relative to this script (assuming script is in code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories to ensure exist
DIRECTORIES = [
    "data/raw",
    "data/processed",
    "data/logs",
    "state"
]

# Files to initialize if missing
STATE_FILE = "state/pipeline_state.json"


def ensure_directory(dir_path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    else:
        if not dir_path.is_dir():
            raise RuntimeError(f"Path exists but is not a directory: {dir_path}")


def initialize_file(file_path: Path, initial_content: dict) -> None:
    """Initialize a JSON state file if it doesn't exist."""
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(initial_content, f, indent=2)
        print(f"Initialized state file: {file_path}")
    else:
        # Validate existing file is valid JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError:
            raise RuntimeError(f"State file exists but is not valid JSON: {file_path}")


def main() -> None:
    """Main entry point for T004."""
    print(f"Setting up data structure for project at: {PROJECT_ROOT}")
    
    # Ensure all required directories exist
    for dir_name in DIRECTORIES:
        dir_path = PROJECT_ROOT / dir_name
        ensure_directory(dir_path)
    
    # Initialize state tracking file
    state_path = PROJECT_ROOT / STATE_FILE
    if not state_path.exists():
        initial_state = {
            "pipeline_version": "1.0.0",
            "last_run": None,
            "tasks_completed": [],
            "data_sources": [],
            "checksums": {},
            "config": {
                "random_seed": 42,
                "splits": 5,
                "model_params": {}
            }
        }
        initialize_file(state_path, initial_state)
    else:
        print(f"State file already exists: {state_path}")
    
    print("Data structure setup complete.")


if __name__ == "__main__":
    main()
