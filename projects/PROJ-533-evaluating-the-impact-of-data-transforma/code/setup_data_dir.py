import os
import sys
from pathlib import Path

def main():
    """
    Create the 'data/' directory using mkdir -p logic and verify its existence.
    This script fulfills task T001b: Create data/ directory and verify.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"

    # Create directory if it doesn't exist (mkdir -p equivalent)
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully created or verified directory: {data_dir}")
    except OSError as e:
        print(f"Error creating directory {data_dir}: {e}", file=sys.stderr)
        sys.exit(1)

    # Verify existence (test -d equivalent)
    if not data_dir.is_dir():
        print(f"Verification failed: {data_dir} is not a directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Verification successful: {data_dir} exists and is a directory.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
