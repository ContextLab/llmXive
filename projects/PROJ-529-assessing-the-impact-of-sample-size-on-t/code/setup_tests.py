"""
Setup script for creating the tests directory structure.
This script creates the necessary directory hierarchy for unit and integration tests.
"""
import os
import sys
from pathlib import Path

def create_tests_directory_structure():
    """
    Creates the tests directory structure with unit and integration subdirectories.
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Define the project root (assuming code/ is at project root level)
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    unit_dir = tests_dir / "unit"
    integration_dir = tests_dir / "integration"
    
    try:
        # Create the directory structure
        tests_dir.mkdir(parents=True, exist_ok=True)
        unit_dir.mkdir(parents=True, exist_ok=True)
        integration_dir.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files to make directories into packages
        (tests_dir / "__init__.py").touch()
        (unit_dir / "__init__.py").touch()
        (integration_dir / "__init__.py").touch()
        
        print(f"Successfully created tests directory structure:")
        print(f"  - {tests_dir}")
        print(f"  - {unit_dir}")
        print(f"  - {integration_dir}")
        
        return True
    except Exception as e:
        print(f"Error creating tests directory structure: {e}", file=sys.stderr)
        return False

def main():
    """Main entry point for the script."""
    success = create_tests_directory_structure()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
