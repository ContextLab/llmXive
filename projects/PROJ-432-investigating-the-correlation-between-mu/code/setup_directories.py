import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure as defined in the implementation plan.
    Directories created relative to the project root.
    """
    # Define the root directory (assuming script is in code/ or project root)
    # We use the current working directory as the project root for safety
    project_root = Path.cwd()
    
    # Define required directories relative to project root
    # Based on T001a description: src/, tests/, data/raw/, data/processed/, data/results/, logs/, config/
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "logs",
        "config",
        # Ensure src subdirectories exist if referenced in API surface
        "src/data",
        "src/analysis",
        "tests/unit",
        "tests/integration",
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Creating project directories in: {project_root}")
    
    for dir_name in directories:
        target_path = project_root / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {target_path}")
            created_count += 1
        else:
            # Check if it's actually a directory
            if target_path.is_dir():
                existing_count += 1
            else:
                print(f"Warning: Path exists but is not a directory: {target_path}")
    
    print(f"\nDirectory creation complete.")
    print(f"Created: {created_count} new directories.")
    print(f"Skipped: {existing_count} existing directories.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())