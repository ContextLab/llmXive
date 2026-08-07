"""
Setup script for llmXive data directory structure.
Creates the required directories for raw, derived, gold standard data and artifacts.
"""
import os
from pathlib import Path
import sys

def setup_directories():
    """
    Creates the standard data directory structure for the project.
    Directories created:
      - data/raw/
      - data/derived/
      - data/gold_standard/
      - artifacts/
    
    Returns:
        dict: Mapping of directory names to their Path objects.
    """
    base_path = Path.cwd()
    
    # Define required directories relative to project root
    data_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "derived",
        base_path / "data" / "gold_standard",
        base_path / "artifacts"
    ]
    
    created_dirs = []
    for dir_path in data_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Verify all directories exist
    missing_dirs = [str(d) for d in data_dirs if not d.exists()]
    if missing_dirs:
        print(f"ERROR: Failed to create directories: {missing_dirs}")
        sys.exit(1)
    
    print(f"\nSuccessfully set up {len(created_dirs)} directories.")
    return {
        "raw": data_dirs[0],
        "derived": data_dirs[1],
        "gold_standard": data_dirs[2],
        "artifacts": data_dirs[3]
    }

if __name__ == "__main__":
    setup_directories()