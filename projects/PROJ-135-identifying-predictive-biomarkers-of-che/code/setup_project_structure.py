"""
Script to initialize the project directory structure for PROJ-135.
Creates all required directories as specified in tasks.md (T001).
"""
import os
import sys
from pathlib import Path

def create_structure():
    # Define the project root (current directory)
    root = Path(".")
    
    # Define the required directory structure relative to the root
    # Based on T001 requirements:
    # src/, data/raw/, data/processed/, results/, results/meta_analysis/, 
    # tests/, specs/001-chemo-biomarker-discovery/contracts/, state/
    
    directories = [
        "code",  # Renamed from 'src' to match project path conventions in prompt
        "code/src",
        "data/raw",
        "data/processed",
        "results",
        "results/meta_analysis",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "specs/001-chemo-biomarker-discovery/contracts",
        "state",
        "figures"
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1
            # Only print if it's a leaf directory we care about, or if verbose
            # print(f"Directory already exists: {full_path}")

    print(f"\nProject structure initialization complete.")
    print(f"Created {created_count} new directories.")
    print(f"Skipped {existing_count} existing directories.")
    
    # Verify critical directories exist
    critical_dirs = [
        "code/src",
        "data/raw",
        "data/processed",
        "results/meta_analysis",
        "tests",
        "specs/001-chemo-biomarker-discovery/contracts",
        "state"
    ]
    
    missing = [d for d in critical_dirs if not (root / d).exists()]
    if missing:
        print(f"ERROR: Critical directories missing: {missing}")
        sys.exit(1)
    else:
        print("All critical directories verified.")

if __name__ == "__main__":
    create_structure()