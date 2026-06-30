"""
Task T001b: Create data directory structure.

Creates the required directory hierarchy for the project's data storage:
- data/raw: For downloaded raw datasets (e.g., OpenNeuro ds000246)
- data/derivatives: For intermediate processing outputs (e.g., fmriprep derivatives)
- data/processed: For final analysis-ready datasets and results
"""
import os
import sys
from pathlib import Path

def main():
    """Create the data directory structure."""
    # Determine project root based on the known structure from T001a
    # The project root is the parent of the 'code' directory
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define the data directory paths
    data_base = project_root / "data"
    directories = [
        data_base / "raw",
        data_base / "derivatives",
        data_base / "processed",
    ]

    # Create directories
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    # Verify structure
    print(f"\nData directory structure verification:")
    for dir_path in directories:
        if dir_path.exists():
            print(f"  [OK] {dir_path.relative_to(project_root)}")
        else:
            print(f"  [FAIL] {dir_path.relative_to(project_root)} - Missing!")
            return 1

    print(f"\nSuccessfully created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
