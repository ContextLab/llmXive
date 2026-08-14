"""
T004 Implementation: Setup data directory structure and .gitkeep files.

This script ensures the existence of the required data directories
(data/raw/, data/processed/, data/results/) and creates .gitkeep files
within them to ensure the directories are tracked by Git even when empty.

Note: T001c creates the directories; this task adds the placeholder files.
"""
import os
import sys
from pathlib import Path

def setup_data_gitkeep_files():
    """
    Creates .gitkeep files in the data subdirectories.
    
    Directories:
        - data/raw/
        - data/processed/
        - data/results/
    """
    # Define the project root relative to this script's location
    # The script is at: projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/setup_data_gitkeep.py
    # The data root is at: projects/PROJ-582-socratic-transformers-dialogue-based-sel/
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent
    data_root = project_root / "data"
    
    required_dirs = ["raw", "processed", "results"]
    created_files = []
    
    for dir_name in required_dirs:
        target_dir = data_root / dir_name
        
        # Ensure the directory exists (idempotent operation)
        if not target_dir.exists():
            print(f"Warning: Directory {target_dir} does not exist. Creating it.")
            target_dir.mkdir(parents=True, exist_ok=True)
        
        gitkeep_path = target_dir / ".gitkeep"
        
        # Create .gitkeep if it doesn't exist
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            created_files.append(str(gitkeep_path))
            print(f"Created: {gitkeep_path}")
        else:
            print(f"Exists: {gitkeep_path}")
    
    return created_files

def verify_gitkeep_files():
    """
    Verifies that all required .gitkeep files exist.
    """
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent
    data_root = project_root / "data"
    
    required_dirs = ["raw", "processed", "results"]
    all_present = True
    
    for dir_name in required_dirs:
        target_dir = data_root / dir_name
        gitkeep_path = target_dir / ".gitkeep"
        
        if not gitkeep_path.exists():
            print(f"FAIL: Missing {gitkeep_path}")
            all_present = False
        else:
            print(f"OK: Found {gitkeep_path}")
    
    return all_present

def main():
    print("=== T004: Setup Data GitKeep Files ===")
    setup_data_gitkeep_files()
    print("-" * 30)
    if verify_gitkeep_files():
        print("SUCCESS: All .gitkeep files present.")
        sys.exit(0)
    else:
        print("FAILURE: Some .gitkeep files are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
