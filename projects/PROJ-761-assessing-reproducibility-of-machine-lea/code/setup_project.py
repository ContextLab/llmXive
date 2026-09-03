"""
Project setup script for PROJ-761-assessing-reproducibility-of-machine-lea.
Creates the required directory structure as per the implementation plan.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the required directories
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/logs",
        "artifacts/plots",
        "artifacts/reports",
        "contracts"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1
            print(f"Directory already exists: {full_path}")
    
    print(f"\nSetup complete: {created_count} new directories created, {existing_count} already existed.")
    
    # Verify structure
    print("\nVerifying directory structure:")
    for dir_path in directories:
        full_path = base_dir / dir_path
        if full_path.exists():
            print(f"  [OK] {full_path}")
        else:
            print(f"  [FAIL] {full_path}")
            sys.exit(1)

if __name__ == "__main__":
    main()
