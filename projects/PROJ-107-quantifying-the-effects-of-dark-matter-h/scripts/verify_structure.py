"""
Verification script for project directory structure.
Checks that all required directories for T001a, T001b, T001c exist.
"""
import os
import sys
from pathlib import Path

REQUIRED_DIRS = [
    # Code Structure
    "code",
    "code/ingestion",
    "code/processing",
    "code/analysis",
    "code/utils",
    "code/tests",
    
    # Data Structure
    "data",
    "data/raw/tng100",
    "data/raw/millennium",
    "data/processed",
    "data/metadata",
    
    # Output Structure
    "outputs",
    "outputs/figures",
    "outputs/reports",
    
    # Docs
    "docs"
]

def verify_structure():
    """
    Verifies the existence of all required directories.
    Returns True if all exist, False otherwise.
    """
    project_root = Path(__file__).parent.parent
    missing = []

    print("Verifying project structure...")
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        if not full_path.is_dir():
            missing.append(dir_path)
            print(f"❌ Missing: {dir_path}")
        else:
            print(f"✅ Found: {dir_path}")

    if missing:
        print(f"\nVerification FAILED. Missing {len(missing)} directories.")
        return False
    
    print(f"\nVerification PASSED. All {len(REQUIRED_DIRS)} directories found.")
    return True

if __name__ == "__main__":
    success = verify_structure()
    sys.exit(0 if success else 1)