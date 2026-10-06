"""
Script to set up the data directory structure for the molecular properties project.
Creates raw/, preprocessed/, and external/ subdirectories under data/.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required data directory structure."""
    # Define the project root (assuming code/scripts/ is two levels deep from root)
    # We navigate up to the project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"

    # Define subdirectories as per task T007
    subdirs = ["raw", "preprocessed", "external"]

    print(f"Setting up data directories in: {data_dir}")

    # Create the main data directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created/Verified: {data_dir}")

    # Create subdirectories
    for subdir_name in subdirs:
        subdir_path = data_dir / subdir_name
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {subdir_path}")
        else:
            print(f"Exists: {subdir_path}")

    # Verify the structure
    print("\nVerification of data directory structure:")
    for subdir_name in subdirs:
        subdir_path = data_dir / subdir_name
        if subdir_path.exists() and subdir_path.is_dir():
            print(f"  [OK] {subdir_path}")
        else:
            print(f"  [FAIL] {subdir_path} does not exist or is not a directory")
            sys.exit(1)

    print("\nData directory structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
