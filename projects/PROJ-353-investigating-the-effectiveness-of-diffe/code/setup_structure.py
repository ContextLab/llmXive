"""
T001: Create project structure per implementation plan.

This script initializes the directory structure required for the project:
- code/
- tests/
- data/raw/
- data/logs/
- data/analysis/
- figures/
- contracts/
- specs/

It creates these directories relative to the project root (where this script is run).
"""
import os
import sys
from pathlib import Path

def main():
    # Define the root directory (current working directory)
    root = Path.cwd()
    
    # Define the directory structure to create
    # Based on plan.md and tasks.md requirements
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/logs",
        "data/analysis",
        "figures",
        "contracts",
        "specs"
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Creating project structure in: {root}")
    
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists (skipped): {full_path}")
            skipped_count += 1
    
    print(f"\nSummary: {created_count} directories created, {skipped_count} already existed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
