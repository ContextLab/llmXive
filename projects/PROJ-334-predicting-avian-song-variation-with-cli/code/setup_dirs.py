import os
import sys
from pathlib import Path

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def initialize_checksums_file(path: Path) -> None:
    """Initialize the checksums file with a header."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write("filename,hash\n")

def initialize_state_file(path: Path) -> None:
    """Initialize the state file with an empty artifact_hashes map."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write("artifact_hashes: {}\n")

def main():
    """Main entry point for directory setup."""
    project_root = Path(__file__).parent.parent
    
    # Define directories
    data_dir = project_root / "data"
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"
    
    # Ensure directories exist
    ensure_directory(data_dir)
    ensure_directory(code_dir)
    ensure_directory(tests_dir)
    
    # Initialize checksums file
    checksums_file = data_dir / "checksums.txt"
    initialize_checksums_file(checksums_file)
    
    # Initialize state file
    state_dir = project_root / "state" / "projects"
    state_file = state_dir / "PROJ-334-predicting-avian-song-variation-with-cli.yaml"
    initialize_state_file(state_file)
    
    print("Directory structure initialized successfully.")

if __name__ == "__main__":
    main()