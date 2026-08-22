"""
Verify Setup: Confirm all directories from T001 exist and state/template.yaml is present.

This script is a critical prerequisite for Phase 2. It exits 0 if all required
artifacts are present, and exits 1 otherwise.

Required Directories (from T001):
- src/, src/models/, src/data/, src/training/, src/experiments/, src/utils/
- tests/unit/, tests/integration/
- scripts/
- data/results/, data/logs/, data/configs/
- state/

Required Files:
- state/template.yaml
"""
import os
import sys
from pathlib import Path

def verify_setup() -> bool:
    """
    Verify the existence of all required directories and files.

    Returns:
        bool: True if all checks pass, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    errors = []

    # Define required directories relative to project root
    required_dirs = [
        "src",
        "src/models",
        "src/data",
        "src/training",
        "src/experiments",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "scripts",
        "data/results",
        "data/logs",
        "data/configs",
        "state",
    ]

    # Define required files relative to project root
    required_files = [
        "state/template.yaml",
    ]

    # Check directories
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            errors.append(f"MISSING DIRECTORY: {full_path}")
        elif not full_path.is_dir():
            errors.append(f"NOT A DIRECTORY: {full_path} (is a file)")

    # Check files
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            errors.append(f"MISSING FILE: {full_path}")
        elif not full_path.is_file():
            errors.append(f"NOT A FILE: {full_path} (is a directory)")

    # Report results
    if errors:
        print("SETUP VERIFICATION FAILED")
        print("-" * 40)
        for error in errors:
            print(f"  [ERROR] {error}")
        print("-" * 40)
        print(f"Total errors: {len(errors)}")
        return False
    else:
        print("SETUP VERIFICATION PASSED")
        print("-" * 40)
        print(f"  Checked {len(required_dirs)} directories: OK")
        print(f"  Checked {len(required_files)} files: OK")
        print("-" * 40)
        return True

def main() -> None:
    """Entry point for the verification script."""
    success = verify_setup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()