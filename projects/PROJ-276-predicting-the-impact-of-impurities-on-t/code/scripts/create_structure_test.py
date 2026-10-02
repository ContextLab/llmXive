import os
from pathlib import Path
import sys

def verify_structure():
    """
    Verifies that the directory structure created by T001 exists.
    Returns True if all required directories exist, False otherwise.
    """
    # Determine project root (assuming this script is in code/scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    required_dirs = [
        "src/ingestion",
        "src/modeling",
        "src/visualization",
        "src/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "docs"
    ]

    missing = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.is_dir():
            missing.append(dir_path)

    if missing:
        print("VERIFICATION FAILED: Missing directories:")
        for d in missing:
            print(f"  - {d}")
        return False
    else:
        print("VERIFICATION PASSED: All required directories exist.")
        return True

if __name__ == "__main__":
    success = verify_structure()
    sys.exit(0 if success else 1)
