import os
from pathlib import Path

def main():
    """
    Create all required project directories.
    This script is idempotent and safe to run multiple times.
    """
    project_root = Path(__file__).parent.parent
    
    directories = [
        # Phase 1: Setup
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/figures",
        "specs/001-neural-correlates-of-anticipatory-reward",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nTotal directories created in this run: {created_count}")
    print(f"Total directories ensured: {len(directories)}")
    return 0

if __name__ == "__main__":
    exit(main())