"""
Script to initialize the project's data directory structure.
Creates required directories for raw, derived, gold standard data, and artifacts.
"""
import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the standard data directory structure:
    - data/raw/
    - data/derived/
    - data/gold_standard/
    - artifacts/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the project root relative to the script location
    # Assuming script is at code/scripts/setup_data_dirs.py
    # Project root is code/
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    data_root = project_root / "data"
    artifacts_root = project_root / "artifacts"

    directories = [
        data_root / "raw",
        data_root / "derived",
        data_root / "gold_standard",
        artifacts_root
    ]

    created_count = 0
    for dir_path in directories:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            # Create a .gitkeep file to ensure the directory is tracked by git
            gitkeep_path = dir_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.write_text("# Keep this directory in version control\n")
            print(f"Created/Verified: {dir_path}")
            created_count += 1
        except PermissionError:
            print(f"Error: Permission denied when creating {dir_path}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error: Failed to create {dir_path}: {e}", file=sys.stderr)
            return False

    print(f"Successfully initialized {created_count} directories.")
    return True

def main():
    """Entry point for the script."""
    success = setup_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
