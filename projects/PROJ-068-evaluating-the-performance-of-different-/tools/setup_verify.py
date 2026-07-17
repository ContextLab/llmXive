#!/usr/bin/env python3
"""
Verification script for project directory structure.

This script verifies that all required directories exist as specified in T001.
"""
import os
import sys
from pathlib import Path

# Project root is two levels up from tools/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Required directories from T001
REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "results",
]

def verify_directories() -> bool:
    """Verify that all required directories exist."""
    all_exist = True
    missing = []
    
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            missing.append(full_path)
            all_exist = False
        elif not full_path.is_dir():
            missing.append(f"{full_path} (not a directory)")
            all_exist = False
    
    return all_exist, missing

def main() -> int:
    """Main entry point for verification."""
    print(f"Verifying project structure in: {PROJECT_ROOT}")
    print("-" * 50)
    
    success, missing = verify_directories()
    
    if success:
        print("✓ All required directories exist:")
        for dir_path in REQUIRED_DIRS:
            print(f"  - {PROJECT_ROOT / dir_path}")
        print("\nVerification PASSED.")
        return 0
    else:
        print("✗ Missing or invalid directories:")
        for item in missing:
            print(f"  - {item}")
        print("\nVerification FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(main())