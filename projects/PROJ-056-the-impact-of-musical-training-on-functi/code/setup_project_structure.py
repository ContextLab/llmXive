import os
import sys
from pathlib import Path

def create_project_structure():
    """
    Creates the project directory structure for PROJ-056.
    This function ensures all necessary folders exist as per the implementation plan.
    """
    # Define the base project directory
    project_root = Path("projects/PROJ-056-the-impact-of-musical-training-on-functi")
    
    # Define all subdirectories to be created
    directories = [
        # Code structure
        project_root / "code" / "data",
        project_root / "code" / "analysis",
        project_root / "code" / "utils",
        
        # Tests structure
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
        
        # Data structure
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        
        # Specs and contracts
        project_root / "specs" / "001-the-impact-of-musical-training-on-functi",
        project_root / "contracts",
    ]
    
    # Create directories
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created: {directory}")
            created_count += 1
        else:
            print(f"Already exists: {directory}")
    
    print(f"\nProject structure creation complete. {created_count} new directories created.")
    return created_count

if __name__ == "__main__":
    create_project_structure()
