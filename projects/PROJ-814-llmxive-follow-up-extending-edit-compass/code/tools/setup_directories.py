"""
Script to initialize the project directory structure for llmXive.
Creates all required directories for data, code, tests, and outputs.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required directory structure."""
    # Define the project root (assuming this script is in code/tools/)
    # We go up two levels to reach the project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent

    # Define all required directories relative to project root
    directories = [
        # Source code directories
        "src/services",
        "src/models",
        "src/utils",
        "src/data-models",
        "src/cli",
        
        # Test directories
        "tests/unit",
        "tests/contract",
        
        # Data directories
        "data/raw",
        "data/filtered",
        "data/scores",
        
        # Output directories
        "outputs",
        "figures",
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            if full_path.exists():
                skipped_count += 1
                print(f"Skipping (exists): {full_path}")
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                created_count += 1
                print(f"Created: {full_path}")
        except Exception as e:
            print(f"Error creating {full_path}: {e}")
            return 1

    print(f"\nDirectory initialization complete.")
    print(f"Created: {created_count}, Skipped: {skipped_count}")
    
    # Verify critical directories exist
    critical_dirs = ["src/services", "data/raw", "data/filtered", "outputs"]
    missing = []
    for d in critical_dirs:
        if not (project_root / d).exists():
            missing.append(d)
    
    if missing:
        print(f"Warning: Missing critical directories: {missing}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
