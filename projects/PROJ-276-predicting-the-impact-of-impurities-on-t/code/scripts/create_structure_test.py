"""
Simple test script to verify the directory structure was created.
This serves as evidence for T001 completion.
"""
import os
from pathlib import Path
import sys

def verify_structure():
    base_path = Path(__file__).resolve().parent.parent
    required_dirs = [
        "code/src/ingestion",
        "code/src/modeling",
        "code/src/visualization",
        "code/src/utils",
        "code/tests/contract",
        "code/tests/integration",
        "code/tests/unit",
        "code/data/raw",
        "code/data/processed",
        "code/docs",
        "state/contradictions"
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.is_dir():
            missing.append(dir_path)
    
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