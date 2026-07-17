#!/usr/bin/env python3
"""
Verification script to assert existence of all required project directories.

This script is used to verify that the project structure has been correctly
initialized according to the project specification.

Usage:
    python tools/setup_verify.py
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "data/processed",
    "results",
    "results/benchmarks",
    "tools",
    "specs",
]

def verify_directories() -> Tuple[bool, List[str]]:
    """Verify that all required directories exist."""
    missing = []
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            missing.append(dir_path)
        elif not full_path.is_dir():
            missing.append(f"{dir_path} (not a directory)")
    
    return len(missing) == 0, missing

def main() -> int:
    """Main entry point."""
    print("Verifying project directory structure...")
    print(f"Project root: {PROJECT_ROOT}")
    
    success, missing = verify_directories()
    
    if missing:
        print("\n❌ VERIFICATION FAILED:")
        print("Missing or invalid directories:")
        for item in missing:
            print(f"  - {item}")
        print("\nPlease run the project setup script to initialize the directory structure.")
        return 1
    
    print("\n✅ All required directories exist.")
    print("Directory structure verification passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
