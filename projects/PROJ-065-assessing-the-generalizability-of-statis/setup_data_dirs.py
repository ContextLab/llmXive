"""
Script to initialize the data directory structure for PROJ-065.
Creates raw and processed data directories with .gitkeep files.
"""
import os
from pathlib import Path

def main():
    # Define project root relative to script location
    project_root = Path(__file__).parent
    data_base = project_root / "data"
    
    raw_dir = data_base / "raw"
    processed_dir = data_base / "processed"
    
    # Ensure base data directory exists
    data_base.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep files to ensure directories are tracked by git
    for dir_path in [raw_dir, processed_dir]:
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text(
                "# Placeholder file to ensure directory is tracked by Git\n"
            )
            print(f"Created: {gitkeep_path}")
        else:
            print(f"Exists: {gitkeep_path}")
    
    print(f"Data directory structure initialized at: {data_base}")

if __name__ == "__main__":
    main()