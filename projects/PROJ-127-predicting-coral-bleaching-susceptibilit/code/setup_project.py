"""
Project Setup Script for PROJ-127-predicting-coral-bleaching-susceptibilit.

This script creates the required directory structure as per the implementation plan:
- code/
- data/raw
- data/processed
- data/models
- tests/
"""
import os
from pathlib import Path

def main():
    # Define the project root (current directory)
    project_root = Path.cwd()
    
    # Define the required directory structure
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/models",
        "tests"
    ]
    
    created_count = 0
    
    print(f"Setting up project structure in: {project_root}")
    
    for dir_path in directories:
        full_path = project_root / dir_path
        
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nSetup complete. {created_count} new directories created.")
    
    # Verify structure
    print("\nVerifying directory structure:")
    for dir_path in directories:
        full_path = project_root / dir_path
        status = "✓" if full_path.exists() else "✗"
        print(f"  {status} {dir_path}")

if __name__ == "__main__":
    main()
