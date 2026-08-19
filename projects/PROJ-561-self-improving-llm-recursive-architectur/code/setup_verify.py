import os
import sys
from pathlib import Path

def verify_project_structure():
    """
    Verifies that the required project directory structure exists.
    Returns True if all required directories and __init__.py files exist, False otherwise.
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "tests",
        "tests/unit",
        "tests/integration"
    ]

    required_init_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py"
    ]

    all_good = True
    missing_dirs = []
    missing_inits = []

    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing_dirs.append(str(full_path))
            all_good = False

    for init_path in required_init_files:
        full_path = base_dir / init_path
        if not full_path.exists():
            missing_inits.append(str(full_path))
            all_good = False

    if all_good:
        print("Project structure verification: PASSED")
        print(f"Base directory: {base_dir}")
        print("All required directories exist:")
        for d in required_dirs:
            print(f"  - {base_dir / d}")
        print("All required __init__.py files exist:")
        for f in required_init_files:
            print(f"  - {base_dir / f}")
        return True
    else:
        print("Project structure verification: FAILED")
        if missing_dirs:
            print("Missing directories:")
            for d in missing_dirs:
                print(f"  - {d}")
        if missing_inits:
            print("Missing __init__.py files:")
            for f in missing_inits:
                print(f"  - {f}")
        return False

if __name__ == "__main__":
    success = verify_project_structure()
    sys.exit(0 if success else 1)
