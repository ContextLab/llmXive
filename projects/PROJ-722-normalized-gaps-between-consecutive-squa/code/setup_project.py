"""
Setup script to create the project directory structure for PROJ-722.
This script implements Task T001 by creating the required directory tree
as defined in the implementation plan.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine the project root relative to this script
    # Assuming the script is run from the project root or the script is in code/
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    # Define the base directory for this specific project instance
    # The task description mentions 'projects/PROJ-normalized-gaps...'
    # but also implies a single project structure. We will create the
    # structure under the current project root as per standard conventions.
    base_name = "PROJ-722-normalized-gaps-between-consecutive-squa"
    base_path = project_root / base_name

    # Define the directory tree components
    # Structure:
    # code/
    # data/raw/
    # data/processed/
    # data/figures/
    # tests/contract/
    # tests/integration/
    # tests/unit/
    # contracts/
    # scripts/
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/figures",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "contracts",
        "scripts"
    ]

    created_count = 0
    skipped_count = 0

    print(f"Creating project structure in: {base_path}")
    
    for dir_name in directories:
        full_path = base_path / dir_name
        
        if full_path.exists():
            print(f"  [SKIP] {full_path.relative_to(project_root)} (exists)")
            skipped_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [OK]   {full_path.relative_to(project_root)}")
            created_count += 1

    print(f"\nSummary: {created_count} directories created, {skipped_count} skipped.")
    print(f"Project structure ready for PROJ-722.")

    return 0

if __name__ == "__main__":
    sys.exit(main())