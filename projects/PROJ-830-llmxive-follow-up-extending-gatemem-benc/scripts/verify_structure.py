"""
Verification script to confirm the project structure was created correctly.
This script checks for the existence of all required directories and files.
"""
import os
import sys
from pathlib import Path

def verify_project_structure():
    """Verify that all required directories and files exist."""
    project_root = Path("projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc")
    
    required_directories = [
        "code/gatekeeper",
        "code/metrics",
        "code/analysis",
        "code/data",
        "data/raw",
        "data/processed",
        "data/logs",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "paper",
        "scripts",
        "specs",
        "config",
    ]
    
    required_files = [
        "code/gatekeeper/__init__.py",
        "code/metrics/__init__.py",
        "code/analysis/__init__.py",
        "code/data/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/contract/__init__.py",
    ]
    
    errors = []
    
    # Check directories
    print("Checking directories...")
    for dir_path in required_directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            errors.append(f"Missing directory: {full_path}")
        elif not full_path.is_dir():
            errors.append(f"Not a directory: {full_path}")
        else:
            print(f"✓ {dir_path}")
    
    # Check files
    print("\nChecking files...")
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            errors.append(f"Missing file: {full_path}")
        elif not full_path.is_file():
            errors.append(f"Not a file: {full_path}")
        else:
            print(f"✓ {file_path}")
    
    # Summary
    print("\n" + "="*50)
    if errors:
        print(f"Verification FAILED with {len(errors)} errors:")
        for error in errors:
            print(f"  ✗ {error}")
        return False
    else:
        print("Verification PASSED: All required directories and files exist.")
        return True

if __name__ == "__main__":
    success = verify_project_structure()
    sys.exit(0 if success else 1)