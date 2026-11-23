"""
Setup script to create project data directories.
Creates the required directory structure for raw, processed, and final data.
"""
import os
import sys
from pathlib import Path

def main():
    # Project root is the parent of the 'code' directory
    # Assuming this script runs from the project root or 'code' directory
    project_root = Path(__file__).parent.parent.resolve()
    project_name = "PROJ-337-predicting-plant-biomass-from-publicly-a"
    
    # Construct the full path for the project directory
    project_dir = project_root / project_name
    
    # Define the data subdirectories required
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/final"
    ]
    
    created_count = 0
    for rel_path in data_dirs:
        full_path = project_dir / rel_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        except PermissionError:
            print(f"Error: Permission denied creating {full_path}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error creating {full_path}: {e}", file=sys.stderr)
            sys.exit(1)
    
    if created_count == len(data_dirs):
        print(f"Successfully created {created_count} data directories under {project_dir}")
        return 0
    else:
        print(f"Warning: Only created {created_count} of {len(data_dirs)} directories.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())