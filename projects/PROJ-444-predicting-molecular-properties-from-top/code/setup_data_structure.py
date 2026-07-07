"""
Task T004: Setup data directory structure and state tracking.

Creates the following directories:
- data/raw/
- data/processed/
- data/logs/
- state/

Initializes state tracking files:
- state/pipeline_state.json (empty state object)
- .gitkeep files in data directories to ensure they are tracked by git.
"""
import os
import json
from pathlib import Path

# Define project root relative to this script's location
# Assuming script is in code/, project root is one level up
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory structure to create
DIRECTORIES = [
    "data/raw",
    "data/processed",
    "data/logs",
    "state",
    "figures"
]

# Files to initialize
INIT_FILES = {
    "state/pipeline_state.json": {},
    "data/raw/.gitkeep": "",
    "data/processed/.gitkeep": "",
    "data/logs/.gitkeep": "",
    "state/.gitkeep": "",
    "figures/.gitkeep": ""
}

def ensure_directory(path: Path) -> None:
    """Create directory if it doesn't exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def initialize_file(path: Path, content) -> None:
    """Write content to file if it doesn't exist."""
    if not path.exists():
        with open(path, 'w') as f:
            if isinstance(content, dict):
                json.dump(content, f, indent=2)
            else:
                f.write(str(content))
        print(f"Initialized file: {path}")
    else:
        print(f"File already exists: {path}")

def main():
    """Main entry point for T004."""
    print(f"Project Root: {PROJECT_ROOT}")
    
    # Create directories
    for dir_path in DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        ensure_directory(full_path)
    
    # Initialize files
    for file_path_str, content in INIT_FILES.items():
        full_path = PROJECT_ROOT / file_path_str
        # Ensure parent directory exists before writing file
        ensure_directory(full_path.parent)
        initialize_file(full_path, content)
    
    print("Data structure and state tracking setup complete.")

if __name__ == "__main__":
    main()