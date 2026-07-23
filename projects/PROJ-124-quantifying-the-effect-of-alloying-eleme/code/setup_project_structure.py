import os
from pathlib import Path

def create_project_structure():
    """
    Creates the project directory structure as defined in the implementation plan.
    This script ensures all required directories exist for the llmXive pipeline.
    """
    # Define the root directory (current working directory or specified project root)
    # Assuming the script is run from the project root
    root = Path.cwd()

    # Define the directory structure relative to root
    directories = [
        # Code structure
        "code/data",
        "code/models",
        "code/utils",
        "code/config",
        
        # Data structure
        "data/raw",
        "data/processed",
        
        # State and output
        "state",
        "output",
        
        # Tests
        "tests/contract",
        "tests/integration",
        "tests/unit",
        
        # Documentation
        "docs/paper",
        "docs/reports",
    ]

    created_count = 0
    skipped_count = 0

    print(f"Creating project structure in: {root}")
    
    for dir_path in directories:
        full_path = root / dir_path
        try:
            if full_path.exists():
                print(f"  [SKIP] {dir_path} (already exists)")
                skipped_count += 1
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATED] {dir_path}")
                created_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to create {dir_path}: {e}")

    print(f"\nSummary: {created_count} directories created, {skipped_count} already existed.")
    return created_count == len(directories) or skipped_count > 0

def main():
    success = create_project_structure()
    if success:
        print("Project structure setup completed successfully.")
        exit(0)
    else:
        print("Project structure setup encountered errors.")
        exit(1)

if __name__ == "__main__":
    main()
