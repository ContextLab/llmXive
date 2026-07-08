"""
Setup script to initialize the project directory structure.
Creates all required directories as per the implementation plan.
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    base_dir = Path(".")
    
    # Define all required directories
    directories = [
        "code",
        "data",
        "paper",
        "contracts",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "paper/figures",
        # Additional standard directories often needed
        "code/lib",
        "code/scripts",
        "code/tests",
        "code/tests/contract",
        "code/tests/integration",
        "specs",
        "docs",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure initialization complete.")
    print(f"Created {created_count} new directories.")
    
    # Verify the structure
    print("\nVerifying directory structure...")
    required_dirs = [
        "code", "data", "paper", "contracts", "tests",
        "data/raw", "data/processed", "data/results", "paper/figures"
    ]
    
    missing = []
    for d in required_dirs:
        if not (base_dir / d).exists():
            missing.append(d)
    
    if missing:
        print(f"ERROR: Missing required directories: {missing}")
        return 1
    else:
        print("All required directories verified.")
        return 0

if __name__ == "__main__":
    exit(main())
