"""
Project initialization script.
Creates the required directory structure for the llmXive automated science pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure as defined in the implementation plan."""
    # Define the base project root (assuming script is run from project root or code/)
    # We use the parent of this script's directory to ensure we hit the project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define the directories to create relative to project root
    directories = [
        "code/data",
        "code/analysis",
        "data/raw",
        "data/processed",
        "data/baseline_corpus",
        "tests/unit",
        "tests/integration",
        "docs/reports"
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1
            # print(f"Directory already exists: {full_path}")

    print(f"Project structure initialization complete.")
    print(f"  New directories created: {created_count}")
    print(f"  Existing directories: {existing_count}")

    # Verify structure
    missing = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing.append(dir_path)
    
    if missing:
        print(f"ERROR: Failed to create the following directories: {missing}")
        sys.exit(1)
    else:
        print("Verification: All required directories exist.")
        sys.exit(0)

if __name__ == "__main__":
    main()
