"""
Setup script to create and verify the 'code/' directory.
This implements Task T001a: Create `code/` directory and verify existence.
"""
import os
import sys
from pathlib import Path


def main() -> int:
    """
    Creates the 'code/' directory if it doesn't exist and verifies it.
    
    Returns:
        int: 0 on success, 1 on failure.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    # Create directory if it doesn't exist (mkdir -p behavior)
    try:
        code_dir.mkdir(parents=True, exist_ok=True)
        print(f"Directory '{code_dir}' created successfully (or already exists).")
    except OSError as e:
        print(f"Error creating directory '{code_dir}': {e}", file=sys.stderr)
        return 1

    # Verify existence (test -d behavior)
    if code_dir.is_dir():
        print(f"Verification successful: '{code_dir}' exists and is a directory.")
        return 0
    else:
        print(f"Verification failed: '{code_dir}' does not exist or is not a directory.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())