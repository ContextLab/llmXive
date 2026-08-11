import os
import sys
from pathlib import Path

def verify_project_structure():
    """
    Verifies the existence of all required directories and __init__.py files.
    Returns True if all checks pass, False otherwise.
    """
    root = Path(__file__).parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "tests",
        "tests/unit",
        "tests/integration",
    ]

    required_init_paths = [
        "code/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "results/__init__.py",
    ]

    all_good = True
    missing_dirs = []
    missing_inits = []

    for dir_path in required_dirs:
        full_path = root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing_dirs.append(str(full_path))
            all_good = False
        else:
            print(f"Directory exists: {full_path}")

    for init_path in required_init_paths:
        full_path = root / init_path
        if not full_path.exists() or not full_path.is_file():
            missing_inits.append(str(full_path))
            all_good = False
        else:
            print(f"Init file exists: {full_path}")

    if missing_dirs:
        print(f"ERROR: Missing directories: {missing_dirs}")
    if missing_inits:
        print(f"ERROR: Missing __init__.py files: {missing_inits}")

    if all_good:
        print("SUCCESS: All required directories and files exist.")
    else:
        print("FAILURE: Verification failed.")
    
    return all_good

if __name__ == "__main__":
    success = verify_project_structure()
    sys.exit(0 if success else 1)
