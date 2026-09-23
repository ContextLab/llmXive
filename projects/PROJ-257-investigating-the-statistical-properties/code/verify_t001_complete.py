"""
Verification script for T001: Initialize Project Directory Structure.
This script checks for the existence of all required directories and
prints a verification report to stdout.
"""
import os
import sys
from pathlib import Path

def verify_t001_complete() -> bool:
    """
    Verify that all required directories for T001 exist.
    
    Required directories:
    - src/, tests/, data/raw/, data/processed/, output/results/, output/figures/, logs/
    - src/data/, src/analysis/, src/viz/, src/utils/
    - tests/unit/, tests/integration/, tests/contract/
    
    Returns:
        bool: True if all directories exist, False otherwise.
    """
    required_dirs = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "output/results",
        "output/figures",
        "logs",
        "src/data",
        "src/analysis",
        "src/viz",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    all_exist = True
    missing_dirs = []
    
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if full_path.is_dir():
            print(f"[OK] {dir_path} exists")
        else:
            print(f"[MISSING] {dir_path} does not exist")
            missing_dirs.append(dir_path)
            all_exist = False
    
    if all_exist:
        print("\n✅ T001 Verification PASSED: All required directories exist.")
    else:
        print(f"\n❌ T001 Verification FAILED: Missing directories: {missing_dirs}")
    
    return all_exist

def main():
    """Main entry point for verification."""
    success = verify_t001_complete()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()