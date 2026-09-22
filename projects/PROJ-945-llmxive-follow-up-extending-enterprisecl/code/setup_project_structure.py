import os
from pathlib import Path

def main():
    """
    Creates the required project directory structure for llmXive.
    Executes the equivalent of:
    mkdir -p src/features src/modeling src/intervention src/eval src/utils data/raw data/processed data/results data/models tests/unit tests/integration tests/contract
    """
    base_dir = Path.cwd()
    
    # Define all required relative paths
    directories = [
        "src/features",
        "src/modeling",
        "src/intervention",
        "src/eval",
        "src/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "data/models",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {full_path}")
        else:
            existing_count += 1
            print(f"Exists: {full_path}")
    
    print(f"\nProject structure setup complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories already existing: {existing_count}")
    
    # Verify the structure by listing created directories
    print("\nVerification of directory structure:")
    for dir_path in directories:
        full_path = base_dir / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path} - Missing or not a directory")

if __name__ == "__main__":
    main()