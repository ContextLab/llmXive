"""
Setup script to create the 'results' directory and verify its existence.
This task corresponds to T001c in the project plan.
"""
import os
import sys
from pathlib import Path


def main():
    """
    Creates the 'results' directory at the project root and verifies it exists.
    Exits with code 0 on success, 1 on failure.
    """
    project_root = Path(__file__).resolve().parent.parent
    results_dir = project_root / "results"

    try:
        # Create the directory if it doesn't exist, including parents if needed
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify existence
        if not results_dir.exists():
            print("ERROR: Failed to create 'results' directory.", file=sys.stderr)
            sys.exit(1)
        
        if not results_dir.is_dir():
            print("ERROR: 'results' path exists but is not a directory.", file=sys.stderr)
            sys.exit(1)

        print(f"Successfully created and verified directory: {results_dir}")
        sys.exit(0)

    except PermissionError:
        print(f"ERROR: Permission denied creating directory: {results_dir}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"ERROR: OS error creating directory: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()