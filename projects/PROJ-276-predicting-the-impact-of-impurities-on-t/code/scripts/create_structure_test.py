import os
from pathlib import Path
import sys

def verify_structure(base_path: Path = None) -> bool:
    """
    Verifies that the required project directories exist.
    Returns True if all directories are present, False otherwise.
    """
    if base_path is None:
        base_path = Path(__file__).resolve().parent.parent

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
    for dir_str in required_dirs:
        full_path = base_path / dir_str
        if not full_path.is_dir():
            missing.append(dir_str)

    if missing:
        print(f"Structure verification FAILED. Missing directories:")
        for m in missing:
            print(f"  - {m}")
        return False
    
    print("Structure verification PASSED. All required directories exist.")
    return True

if __name__ == "__main__":
    success = verify_structure()
    sys.exit(0 if success else 1)
