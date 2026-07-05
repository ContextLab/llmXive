"""
Script to create the project directory structure for the muon flux study.

This script creates the following directories relative to the project root:
- src/
- tests/
- data/raw/
- data/processed/
- data/results/
- logs/
- config/
"""
import os
import sys
from pathlib import Path

# Define the directory structure relative to the project root
DIRECTORIES = [
    "src",
    "tests",
    "data/raw",
    "data/processed",
    "data/results",
    "logs",
    "config",
]

def main():
    # Determine project root (current working directory)
    project_root = Path.cwd()
    
    print(f"Creating directory structure in: {project_root}")
    
    created_count = 0
    for dir_path in DIRECTORIES:
        full_path = project_root / dir_path
        
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {full_path}")
            created_count += 1
        else:
            print(f"  Exists: {full_path}")
    
    print(f"\nSetup complete. Created {created_count} new directories.")
    
    # Verify structure
    missing = []
    for dir_path in DIRECTORIES:
        if not (project_root / dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"ERROR: Missing directories: {missing}")
        sys.exit(1)
    else:
        print("Verification passed: All required directories exist.")

if __name__ == "__main__":
    main()