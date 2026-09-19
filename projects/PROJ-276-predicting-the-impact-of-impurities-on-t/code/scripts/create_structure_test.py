import os
from pathlib import Path
import sys

def verify_structure():
    """Verify that all required directories from T001 exist."""
    base_path = Path(__file__).parent.parent  # points to code/
    
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
    for dir_name in required_dirs:
        full_path = base_path / dir_name
        if not full_path.is_dir():
            missing.append(str(full_path))
    
    if missing:
        print("ERROR: The following directories are missing:")
        for m in missing:
            print(f"  - {m}")
        return False
    
    print("SUCCESS: All required directories exist.")
    return True

if __name__ == "__main__":
    success = verify_structure()
    sys.exit(0 if success else 1)
