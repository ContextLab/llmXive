"""
Script to create the required data directory structure.
This addresses the rejection of T004 by providing an executable script
that creates the directories on disk.
"""
import sys
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_dirs = [
        base_dir / "data" / "raw",
        base_dir / "data" / "results",
        base_dir / "data" / "figures",
    ]

    for directory in data_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {directory}")

    # Verify existence
    for directory in data_dirs:
        if not directory.is_dir():
            print(f"Error: Failed to create {directory}", file=sys.stderr)
            sys.exit(1)

    print("Data directory structure successfully created.")
    sys.exit(0)

if __name__ == "__main__":
    main()