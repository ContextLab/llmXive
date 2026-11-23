"""
Script to initialize the data directory structure for the llmXive project.

This script creates the necessary directories (data/raw, data/processed)
and places .gitkeep files to ensure they are tracked by git even when empty.

Usage:
    python code/setup_data_dirs.py
"""
import os
from pathlib import Path
import sys

def main():
    """Create the data directory structure."""
    # Get project root (assuming this script is in code/)
    project_root = Path(__file__).resolve().parent.parent
    
    # Define data directories
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    
    # Create directories if they don't exist
    for directory in [data_raw, data_processed]:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")
    
    # Create .gitkeep files to ensure directories are tracked
    gitkeep_raw = data_raw / ".gitkeep"
    gitkeep_processed = data_processed / ".gitkeep"
    
    for gitkeep in [gitkeep_raw, gitkeep_processed]:
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep file: {gitkeep}")
        else:
            print(f".gitkeep file already exists: {gitkeep}")
    
    print("\nData directory structure initialization complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())