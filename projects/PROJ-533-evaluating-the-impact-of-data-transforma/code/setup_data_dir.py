"""
Setup script to create the 'data/' directory and verify its existence.

This script implements Task T001b:
- Creates the 'data/' directory using mkdir -p logic.
- Verifies existence using test -d logic (Python os.path.isdir).
- Prints success message on verification.
- Raises an error if verification fails (Fail loudly).
"""
import os
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"

    # Create directory if it doesn't exist (mkdir -p logic)
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {data_dir}")
    else:
        print(f"Directory already exists: {data_dir}")

    # Verify existence (test -d logic)
    if not data_dir.is_dir():
        error_msg = f"Verification failed: {data_dir} exists but is not a directory."
        print(error_msg, file=sys.stderr)
        raise RuntimeError(error_msg)

    # Additional verification: ensure it's writable (optional but good practice)
    try:
        test_file = data_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        print(f"Verification successful: {data_dir} is a valid, writable directory.")
    except PermissionError:
        error_msg = f"Verification failed: {data_dir} exists but is not writable."
        print(error_msg, file=sys.stderr)
        raise RuntimeError(error_msg)

if __name__ == "__main__":
    main()
