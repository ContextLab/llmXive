import os
import sys
from pathlib import Path
from config import ensure_dirs

def create_directories():
    """
    Create the standard project directory structure for llmXive.
    Ensures all required folders exist under the project root.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data",
        "data/raw",
        "data/intermediate",
        "data/processed",
        "data/provenance",
        "data/results",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        else:
            # Ensure it's actually a directory, not a file
            if not dir_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {dir_path}")
    
    print(f"Directory setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for directory creation."""
    try:
        # Ensure config directories exist first if not already done
        # This script relies on config.py being present
        success = create_directories()
        if success:
            print("SUCCESS: All project directories created.")
            return 0
        else:
            print("ERROR: Directory creation failed.")
            return 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
