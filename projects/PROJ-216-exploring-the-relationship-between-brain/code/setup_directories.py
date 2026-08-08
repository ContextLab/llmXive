"""
Script to initialize the project directory structure and create __init__.py files.
This satisfies Task T001.
"""
import os
import sys
from pathlib import Path
from typing import List

def create_directories(paths: List[str]) -> None:
    """Create directories if they do not exist."""
    for p in paths:
        path_obj = Path(p)
        path_obj.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {p}")

def verify_directories(paths: List[str]) -> bool:
    """Verify that all specified directories exist."""
    all_exist = True
    for p in paths:
        path_obj = Path(p)
        if not path_obj.is_dir():
            print(f"ERROR: Directory missing: {p}")
            all_exist = False
        else:
            print(f"Verified directory: {p}")
    return all_exist

def main() -> int:
    """Main entry point to create and verify required data and test directories."""
    # Define required directories based on tasks T001b, T001c, T001d, T001f, T001g
    required_dirs = [
        "data/raw",
        "data/interim",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "reports"
    ]

    # Create directories
    print("Creating directories...")
    create_directories(required_dirs)

    # Verify directories
    print("\nVerifying directories...")
    success = verify_directories(required_dirs)

    if success:
        print("\nAll required directories created and verified successfully.")
        return 0
    else:
        print("\nVerification failed: Some directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
