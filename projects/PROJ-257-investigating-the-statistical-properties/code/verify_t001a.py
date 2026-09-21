import os
import sys
from pathlib import Path

def verify_t001a():
    """
    Verification script for T001a.
    Runs checks equivalent to:
    test -d src/data
    test -d src/analysis
    test -d src/viz
    test -d src/utils
    """
    root = Path(".")
    required_dirs = [
        "src/data",
        "src/analysis",
        "src/viz",
        "src/utils"
    ]

    all_passed = True
    for rel_path in required_dirs:
        full_path = root / rel_path
        if not full_path.is_dir():
            print(f"FAIL: Directory {full_path} does not exist.")
            all_passed = False
        else:
            print(f"PASS: Directory {full_path} exists.")

    if all_passed:
        print("T001a Verification: SUCCESS")
        sys.exit(0)
    else:
        print("T001a Verification: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    verify_t001a()