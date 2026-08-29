"""
Task T001a: Create data directories for the Cognitive Load Optimization project.

This script creates the required directory structure under the 'data/' directory
using a single mkdir -p command equivalent in Python.

Directories created:
- data/raw/
- data/processed/
- data/explanation_tiers/
- data/simulation_results/
"""
import os
import sys
from pathlib import Path

def main():
    # Define the base data directory relative to the project root
    # We assume this script runs from the project root or code/ directory
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"

    # Define the required subdirectories
    required_dirs = [
        "raw",
        "processed",
        "explanation_tiers",
        "simulation_results"
    ]

    # Construct full paths
    full_paths = [data_root / d for d in required_dirs]

    # Create directories using a single loop (equivalent to mkdir -p)
    # This ensures all parent directories are created if they don't exist
    try:
        for dir_path in full_paths:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")

        # Verify creation
        missing = [d for d in full_paths if not d.exists()]
        if missing:
            print(f"ERROR: Failed to create directories: {missing}", file=sys.stderr)
            sys.exit(1)

        print(f"Successfully created {len(required_dirs)} data directories under {data_root}")
        return 0

    except PermissionError as e:
        print(f"ERROR: Permission denied while creating directories: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error creating directories: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
