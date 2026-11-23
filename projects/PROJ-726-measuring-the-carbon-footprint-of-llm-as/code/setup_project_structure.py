"""
Module to create the project directory structure.
Implements T001: Create project root structure per implementation plan.
"""
import os
import sys
from pathlib import Path

def create_directory_structure(root_dir: str = ".") -> None:
    """
    Creates the required directory structure for the project.
    
    Required directories:
    - code/
    - data/raw/
    - data/processed/
    - data/outputs/
    - tests/unit/
    - tests/contract/
    
    Also creates empty __init__.py files in all code/ and tests/ subdirectories.
    """
    # Define the base project directory (current working directory)
    base_dir = Path.cwd()
    
    # Define required directories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/outputs",
        "tests/unit",
        "tests/contract"
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create __init__.py files in code/ and tests/ subdirectories
    # code/ directory
    code_init = base_dir / "code" / "__init__.py"
    code_init.touch()
    print(f"Created: {code_init}")
    
    # tests/ unit directory
    tests_unit_init = base_dir / "tests" / "unit" / "__init__.py"
    tests_unit_init.parent.mkdir(parents=True, exist_ok=True)
    tests_unit_init.touch()
    print(f"Created: {tests_unit_init}")
    
    # tests/ contract directory
    tests_contract_init = base_dir / "tests" / "contract" / "__init__.py"
    tests_contract_init.parent.mkdir(parents=True, exist_ok=True)
    tests_contract_init.touch()
    print(f"Created: {tests_contract_init}")
    
    # Create root tests/__init__.py
    tests_init = base_dir / "tests" / "__init__.py"
    tests_init.touch()
    print(f"Created: {tests_init}")
    
    print("\nProject structure created successfully!")
    print("Directory structure:")
    for dir_path in directories:
        print(f"  - {dir_path}")
    
    return True

def main():
    """Main entry point for the script."""
    print("Initializing project structure...")
    success = create_directory_structure()
    if success:
        print("Project structure setup complete.")
        return 0
    else:
        print("Project structure setup failed.")
        return 1

if __name__ == "__main__":
    main()