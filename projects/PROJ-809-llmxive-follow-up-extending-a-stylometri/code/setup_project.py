"""
T001: Initialize project directory structure.

Creates the required directory tree for PROJ-809-llmxive-follow-up-extending-a-stylometri
including code/, data/, artifacts/, contracts/, tests/, and state/ with subdirectories.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine project root based on execution context
    # If run as script, assume current working directory is the project root
    # If run from within 'code', go up one level
    script_path = Path(__file__).resolve()
    current_dir = script_path.parent
    
    # Check if we are in 'code' directory
    if current_dir.name == 'code':
        project_root = current_dir.parent
    else:
        project_root = current_dir

    # Define the directory structure to create
    # Base directories
    base_dirs = [
        "code",
        "data",
        "artifacts",
        "contracts",
        "tests",
        "state",
        "docs",
        "specs",
    ]
    
    # Subdirectories
    sub_dirs = [
        # Data structure
        "data/raw",
        "data/processed",
        "data/hybrid",
        
        # Artifacts structure
        "artifacts/models",
        "artifacts/metrics",
        "artifacts/figures",
        
        # Tests structure
        "tests/unit",
        "tests/contract",
        "tests/integration",
    ]
    
    all_dirs = base_dirs + sub_dirs

    created_count = 0
    skipped_count = 0

    for dir_path in all_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            # print(f"Exists: {full_path}") # Optional: reduce noise
            skipped_count += 1

    print(f"\nProject structure initialized at: {project_root}")
    print(f"Directories created: {created_count}")
    print(f"Directories skipped (already exist): {skipped_count}")
    
    # Verify critical directories exist
    critical_paths = [
        "code", "data/processed", "artifacts/models", "tests/unit", "state"
    ]
    missing = []
    for p in critical_paths:
        if not (project_root / p).exists():
            missing.append(p)
    
    if missing:
        print(f"ERROR: Critical directories missing: {missing}")
        sys.exit(1)
    else:
        print("Verification: All critical directories present.")

if __name__ == "__main__":
    main()
