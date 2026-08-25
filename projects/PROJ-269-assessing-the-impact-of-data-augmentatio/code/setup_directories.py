import os
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-269.
    
    Creates the following directories relative to the project root:
    - code/
    - data/raw/
    - data/derived/
    - results/
    - tests/
    - contracts/
    
    This script is idempotent and will not fail if directories already exist.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the required directory structure
    directories = [
        "code",
        "data/raw",
        "data/derived",
        "results",
        "tests",
        "contracts"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1
            print(f"Directory already exists: {full_path}")
    
    print(f"\nDirectory setup complete.")
    print(f"  Created: {created_count}")
    print(f"  Existing: {existing_count}")
    print(f"  Total: {len(directories)}")
    
    # Verify structure
    print("\nVerifying structure:")
    for dir_path in directories:
        full_path = project_root / dir_path
        status = "✓" if full_path.exists() else "✗"
        print(f"  {status} {dir_path}")

if __name__ == "__main__":
    main()
