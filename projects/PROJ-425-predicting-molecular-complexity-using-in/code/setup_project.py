import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for the llmXive pipeline.
    Implements T001: Create project structure per implementation plan.
    
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - reports/figures/
    - tests/unit/
    - tests/contract/
    """
    project_root = Path(".")
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "reports/figures",
        "tests/unit",
        "tests/contract"
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
    
    print(f"\nProject structure initialization complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for script execution."""
    try:
        success = create_directories()
        if success:
            print("T001: Project structure created successfully.")
            sys.exit(0)
        else:
            print("T001: Failed to create project structure.")
            sys.exit(1)
    except Exception as e:
        print(f"Error during directory creation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()