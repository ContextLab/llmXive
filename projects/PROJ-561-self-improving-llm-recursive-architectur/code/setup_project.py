import os
import sys
from pathlib import Path

def create_project_structure():
    """
    Creates the required project directory structure and initializes __init__.py files.
    This implements Task T001: Create project structure per implementation plan.
    
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - results/
    - specs/
    - tests/
    - tests/unit/
    - tests/integration/
    """
    # Define the root directory (project root)
    root = Path(__file__).parent.parent
    
    # Define the required directories relative to the root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "tests",
        "tests/unit",
        "tests/integration",
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Creating project structure in: {root}")
    
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created directory: {full_path}")
            created_count += 1
        else:
            print(f"  Directory already exists: {full_path}")
            skipped_count += 1
        
        # Create __init__.py in each directory to make them Python packages
        # Note: We create __init__.py in all directories as per task requirement
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Package initialization\n")
            print(f"  Created __init__.py: {init_file}")
            created_count += 1
        else:
            print(f"  __init__.py already exists: {init_file}")
            skipped_count += 1
    
    print(f"\nSummary: Created {created_count} items, Skipped {skipped_count} items")
    return True

if __name__ == "__main__":
    success = create_project_structure()
    if success:
        print("Project structure created successfully.")
        sys.exit(0)
    else:
        print("Failed to create project structure.")
        sys.exit(1)
