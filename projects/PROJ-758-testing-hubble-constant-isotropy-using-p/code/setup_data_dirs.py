"""
Script to initialize the data directory structure for the Hubble Constant Isotropy project.
Creates the required directory hierarchy under 'data/' to support the pipeline's
ingestion, processing, and results storage needs.
"""
import os
import sys
from pathlib import Path


def main():
    """
    Creates the data directory structure:
    - data/raw/          : For raw downloaded datasets (e.g., Pantheon+ CSV)
    - data/processed/    : For cleaned, filtered, and spatially indexed data
    - data/results/      : For final analysis outputs (H0 estimates, anisotropy metrics)
    
    Exits with status 0 on success, 1 on failure.
    """
    # Determine the project root. 
    # Based on project structure, this script is in code/, so root is parent.
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    data_root = project_root / "data"
    
    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "results",
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Initializing data directories in: {data_root}")
    
    for dir_path in directories:
        if dir_path.exists():
            if dir_path.is_dir():
                print(f"  [SKIP] {dir_path.relative_to(project_root)} (already exists)")
                existing_count += 1
            else:
                print(f"  [ERROR] {dir_path.relative_to(project_root)} exists but is not a directory")
                return 1
        else:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATED] {dir_path.relative_to(project_root)}")
                created_count += 1
            except OSError as e:
                print(f"  [FAILED] Could not create {dir_path.relative_to(project_root)}: {e}")
                return 1
    
    print(f"\nData directory initialization complete.")
    print(f"  Created: {created_count}")
    print(f"  Existing: {existing_count}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for dir_path in directories:
        keep_file = dir_path / ".gitkeep"
        if not keep_file.exists():
            try:
                keep_file.touch()
            except OSError:
                pass  # Ignore if we can't create .gitkeep, dir creation is the primary goal
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
