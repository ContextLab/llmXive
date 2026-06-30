"""
Task T008: Validate and create the data directory structure.

This script explicitly creates the required data directories:
benchmarks/, generated/, coverage_reports/, processed/, outputs/

It also verifies the existence of subdirectories created in T001b.
"""
import os
import sys
from pathlib import Path
from setup_directories import create_directories

def validate_and_create_data_structure():
    """
    Ensures the full data directory structure exists.
    
    Primary directories (from task description):
    - data/benchmarks/
    - data/generated/
    - data/coverage_reports/
    - data/processed/
    - data/outputs/
    
    Subdirectories (from T001b):
    - data/benchmarks/raw/
    - data/benchmarks/processed/
    - data/benchmarks/processed/tests/ (implied by T007)
    """
    base_path = Path("data")
    
    # Define the primary directories required by T008
    required_dirs = [
        "benchmarks",
        "generated",
        "coverage_reports",
        "processed",
        "outputs"
    ]
    
    # Define subdirectories required by T001b and T007 to ensure completeness
    sub_dirs = [
        "benchmarks/raw",
        "benchmarks/processed",
        "benchmarks/processed/tests",
        "generated", # Already in required, but ensuring it's treated as a target
        "coverage_reports",
        "processed",
        "outputs"
    ]
    
    # Create the base data directory if it doesn't exist
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Use the existing create_directories utility to create the structure
    # We pass the full relative paths from the project root
    all_dirs_to_create = [str(base_path / d) for d in sub_dirs]
    
    # Filter out duplicates and ensure parent directories exist
    unique_dirs = sorted(list(set(all_dirs_to_create)))
    
    print(f"Validating and creating {len(unique_dirs)} directories under 'data/'...")
    
    created_count = 0
    for dir_path in unique_dirs:
        p = Path(dir_path)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {dir_path}")
            created_count += 1
        else:
            print(f"  Exists:  {dir_path}")
    
    # Explicit verification step
    missing = []
    for d in required_dirs:
        full_path = base_path / d
        if not full_path.exists():
            missing.append(d)
    
    if missing:
        print(f"ERROR: Missing required directories: {missing}")
        return False
    
    print(f"Validation complete. {created_count} directories created, all required paths exist.")
    return True

if __name__ == "__main__":
    success = validate_and_create_data_structure()
    sys.exit(0 if success else 1)