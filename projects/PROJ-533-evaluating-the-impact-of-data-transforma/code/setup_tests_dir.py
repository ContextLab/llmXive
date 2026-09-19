"""
Setup script to create the 'tests/' directory structure.
This script ensures the 'tests/' directory exists for the project.
"""
import os
from pathlib import Path

def main():
    """Create the tests/ directory if it doesn't exist."""
    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        tests_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {tests_dir}")
    else:
        print(f"Directory already exists: {tests_dir}")
    
    # Ensure subdirectories for unit and integration tests
    unit_dir = tests_dir / "unit"
    if not unit_dir.exists():
        unit_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {unit_dir}")
        
    integration_dir = tests_dir / "integration"
    if not integration_dir.exists():
        integration_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {integration_dir}")
    
    return 0

if __name__ == "__main__":
    exit(main())
