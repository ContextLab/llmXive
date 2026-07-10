"""
Task T004: Create data directory structure and empty checksums file.

This script ensures the existence of `data/raw/`, `data/processed/`,
and creates an empty `data/checksums.txt` file.
"""
import os
from pathlib import Path

def main():
    # Define project root relative to script location or use current working directory
    # Assuming script is run from project root or code/ directory
    project_root = Path.cwd()
    
    # Ensure we are in the correct project context if run from code/
    if (project_root / "data").exists() or project_root.name == "code":
        if project_root.name == "code":
            project_root = project_root.parent
    
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    checksums_file = data_dir / "checksums.txt"

    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create empty checksums file if it doesn't exist
    if not checksums_file.exists():
        checksums_file.touch()
        print(f"Created: {checksums_file}")
    else:
        print(f"Exists: {checksums_file}")

    print(f"Created/Verified: {raw_dir}")
    print(f"Created/Verified: {processed_dir}")
    print("Data directory structure ready.")

if __name__ == "__main__":
    main()
