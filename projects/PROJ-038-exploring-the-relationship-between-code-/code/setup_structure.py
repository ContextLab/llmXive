import os
from pathlib import Path

def main():
    """
    Creates the required project directory structure for the llmXive science pipeline.
    This script ensures all necessary folders exist before data ingestion or analysis begins.
    """
    base_dir = Path(__file__).parent.parent.resolve()
    
    # Define relative paths as per task T001a
    directories = [
        "code",
        "code/src",
        "code/tests",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
        "specs/001-exploring-the-relationship-between-code"
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
    
    print(f"\nSetup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())