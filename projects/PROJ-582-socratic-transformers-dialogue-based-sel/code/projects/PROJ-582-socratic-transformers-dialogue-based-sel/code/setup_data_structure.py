"""
T001c: Create project data structure.

Creates the required directory hierarchy for data management:
- data/raw/: For original, unprocessed dataset downloads.
- data/processed/: For cleaned, tokenized, or transformed data.
- data/results/: For model checkpoints, evaluation metrics, and logs.

Verification:
Run `python setup_data_structure.py` then `ls -R data` to confirm existence.
"""
import os
import sys
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """Create the standard data directory structure."""
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def verify_structure(base_path: Path) -> bool:
    """Assert that all required directories exist."""
    required_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if not dir_path.is_dir():
            print(f"ERROR: Missing directory: {dir_path}")
            all_exist = False
        else:
            print(f"Verified: {dir_path}")
    
    return all_exist

def main() -> int:
    """Entry point for the script."""
    # Determine project root relative to this file's location
    # Script is at: code/projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/setup_data_structure.py
    # Target is: code/projects/PROJ-582-socratic-transformers-dialogue-based-sel/ (project root)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent 
    
    print(f"Project root detected at: {project_root}")
    
    create_directories(project_root)
    
    if verify_structure(project_root):
        print("\n✅ T001c Verification: All data directories exist.")
        return 0
    else:
        print("\n❌ T001c Verification: Failed. Some directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())