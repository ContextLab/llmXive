"""
Project Setup Script (T001).

This script creates the required directory structure for the llmXive project
as defined in plan.md and tasks.md. It ensures that all necessary directories
for code, tests, and data (with subdirectories) exist.
"""
import os
from pathlib import Path

def main():
    # Define the project root
    project_root = Path(__file__).parent
    
    # Define the directory structure to create
    directories = [
        "code",
        "code/utils",
        "tests",
        "data/raw",
        "data/filtered",
        "data/traces",
        "data/results",
        "data/validation",
        "data/pilot",
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
            # Create .gitkeep to ensure directories are tracked in git
            gitkeep_path = full_path / ".gitkeep"
            gitkeep_path.touch()
        else:
            skipped_count += 1
            # Ensure .gitkeep exists even if dir already existed
            gitkeep_path = full_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.touch()
    
    print(f"\nProject structure setup complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories already existing: {skipped_count}")
    print(f"\nStructure created under: {project_root}")
    print("  - code/ (source code)")
    print("  - tests/ (unit and integration tests)")
    print("  - data/ (raw, filtered, traces, results, validation, pilot)")

if __name__ == "__main__":
    main()