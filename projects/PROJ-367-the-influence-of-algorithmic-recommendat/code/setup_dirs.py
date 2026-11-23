"""
Setup script to create all required project directories for PROJ-367.
This script ensures the directory structure exists as per the project specification.
"""
import os
from pathlib import Path

def main():
    """Create all required project directories."""
    # Define the project root relative to the script location
    # Assuming this script is in projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/
    # We need to go up two levels to reach the project root
    current_path = Path(__file__).resolve()
    project_root = current_path.parent.parent
    
    # Define the relative paths to create
    required_dirs = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "docs",
        "docs/reports"
    ]
    
    created_count = 0
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nTotal directories created: {created_count}")
    print(f"Project root: {project_root}")
    
    # Verify all directories exist
    print("\n--- Verification (ls -R) ---")
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"{dir_path}: OK")
            # List contents if it's not empty
            contents = list(dir_path.iterdir())
            if contents:
                for item in contents:
                    print(f"  - {item.name}")
        else:
            print(f"{dir_path}: MISSING")
            raise FileNotFoundError(f"Required directory not found: {dir_path}")

if __name__ == "__main__":
    main()
