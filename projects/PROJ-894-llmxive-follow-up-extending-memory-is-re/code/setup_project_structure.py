"""
Script to create the project directory structure for PROJ-894-llmxive-follow-up-extending-memory-is-re.
This script ensures all required directories exist relative to the project root.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine the project root based on the script location
    # The script is expected to be run from the project root or code/ directory
    # We assume the current working directory is the project root for safety
    project_root = Path.cwd()
    
    # Define the relative paths required by the task
    # The task specifies: code/, data/, tests/, data/raw, data/processed, data/processed/graphs, data/processed/results
    # And specifically: data/intermediate
    relative_paths = [
        "code",
        "data",
        "tests",
        "data/raw",
        "data/processed",
        "data/processed/graphs",
        "data/processed/results",
        "data/intermediate"
    ]

    created_dirs = []
    errors = []

    for rel_path in relative_paths:
        target_dir = project_root / rel_path
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(target_dir))
            print(f"Created directory: {target_dir}")
        except Exception as e:
            errors.append(f"Failed to create {target_dir}: {e}")
            print(f"Error creating {target_dir}: {e}", file=sys.stderr)

    if errors:
        print(f"\nCompleted with {len(errors)} errors.")
        sys.exit(1)
    else:
        print(f"\nSuccessfully created {len(created_dirs)} directories.")
        # List the structure to confirm
        print("\nProject structure verification:")
        for d in sorted(created_dirs):
            print(f"  {d}")
        sys.exit(0)

if __name__ == "__main__":
    main()