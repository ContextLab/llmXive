import os
import sys
from pathlib import Path
from config import get_project_root

def create_directories():
    """
    Create all required project directories.
    Returns a dictionary mapping directory names to their paths and creation status.
    """
    root = get_project_root()
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/models",
        "outputs",
        "tests",
        "state/projects",
        "code/utils"
    ]

    results = {}
    for dir_name in directories:
        dir_path = root / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            results[dir_name] = {"path": str(dir_path), "status": "created", "exists": True}
        except Exception as e:
            results[dir_name] = {"path": str(dir_path), "status": "failed", "error": str(e), "exists": False}
    
    return results

def main():
    """Entry point for directory creation."""
    print("Creating project directories...")
    results = create_directories()
    
    all_success = True
    for dir_name, info in results.items():
        if info["status"] == "failed":
            print(f"ERROR: Failed to create {dir_name}: {info.get('error')}")
            all_success = False
        else:
            print(f"OK: {dir_name} ({info['path']})")
    
    if not all_success:
        sys.exit(1)
    print("All directories created successfully.")
    return results

if __name__ == "__main__":
    main()
