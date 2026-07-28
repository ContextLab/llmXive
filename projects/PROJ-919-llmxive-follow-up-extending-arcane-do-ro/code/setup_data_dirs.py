"""
Setup script to initialize the data directory structure for the llmXive project.

This script creates the following directories under the project root:
- data/raw: For raw, unprocessed external data
- data/derived: For processed/generated data (axes, probes, results)
- data/gold_standard: For human annotations and validation sets
- artifacts: For model checkpoints, logs, and experiment artifacts

Usage:
    python code/setup_data_dirs.py
"""
import os
from pathlib import Path
import sys

def setup_directories():
    """
    Creates the required data directory structure.
    
    Returns:
        dict: A dictionary mapping directory names to their absolute paths.
    """
    # Determine project root (assuming this script is in code/)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Define the required directories relative to project root
    data_dirs = [
        "data/raw",
        "data/derived",
        "data/gold_standard",
        "artifacts"
    ]
    
    created_dirs = {}
    
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs[dir_path] = str(full_path)
            print(f"✓ Created/Verified directory: {full_path}")
        except OSError as e:
            print(f"✗ Failed to create directory {full_path}: {e}", file=sys.stderr)
            raise
    
    # Create a .gitkeep file in each directory to ensure they are tracked by git
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        keep_file = full_path / ".gitkeep"
        try:
            keep_file.touch(exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create .gitkeep in {full_path}: {e}", file=sys.stderr)
    
    print(f"\nSuccessfully initialized {len(created_dirs)} directories under {project_root}")
    return created_dirs

if __name__ == "__main__":
    setup_directories()
