"""
Verification script for T001: Create project structure.
This script ensures all required directories and initialization files exist.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
REQUIRED_DIRS = [
    "code/synthetic",
    "code/models",
    "code/metrics",
    "code/analysis",
    "tests/unit",
    "tests/contract",
    "data/raw",
    "data/synthetic",
    "data/processed",
    "state",
]

REQUIRED_FILES = [
    "code/__init__.py",
    "code/synthetic/__init__.py",
    "code/models/__init__.py",
    "code/metrics/__init__.py",
    "code/analysis/__init__.py",
    "tests/__init__.py",
    "tests/unit/__init__.py",
    "tests/contract/__init__.py",
    "data/raw/.gitkeep",
    "data/synthetic/.gitkeep",
    "data/processed/.gitkeep",
    "state/.gitkeep",
]

def verify_structure() -> bool:
    """Verify all required directories and files exist."""
    all_good = True

    print(f"Verifying project structure at: {PROJECT_ROOT}")

    # Check directories
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            print(f"❌ Missing directory: {dir_path}")
            all_good = False
        else:
            print(f"✅ Directory exists: {dir_path}")

    # Check files
    for file_path in REQUIRED_FILES:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            print(f"❌ Missing file: {file_path}")
            all_good = False
        else:
            print(f"✅ File exists: {file_path}")

    return all_good

if __name__ == "__main__":
    if verify_structure():
        print("\n✅ All structure checks passed.")
        sys.exit(0)
    else:
        print("\n❌ Structure verification failed.")
        sys.exit(1)