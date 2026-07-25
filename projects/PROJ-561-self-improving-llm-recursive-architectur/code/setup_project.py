"""
Project Structure Setup Script for llmXive.

This script creates the required directory structure and initializes
__init__.py files for all packages as specified in T001.
"""
import os
import sys
from pathlib import Path

def create_project_structure():
    """Create the standard project directory structure."""
    root = Path(__file__).parent.parent
    
    # Define all required directories relative to project root
    directories = [
        "code",
        "code/utils",
        "code/pipeline",
        "code/results",
        "code/schemas",
        "data",
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
    
    for dir_path in directories:
        full_path = root / dir_path
        if full_path.exists():
            skipped_count += 1
            print(f"[SKIP] Directory exists: {full_path}")
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"[CREATE] Directory: {full_path}")
    
    # Initialize __init__.py files for all package directories
    init_files = [
        "code/__init__.py",
        "code/utils/__init__.py",
        "code/pipeline/__init__.py",
        "code/results/__init__.py",
        "code/schemas/__init__.py",
        "data/__init__.py",
        "data/raw/__init__.py",
        "data/processed/__init__.py",
        "results/__init__.py",
        "specs/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
    ]
    
    init_created = 0
    init_skipped = 0
    
    for init_path in init_files:
        full_init = root / init_path
        if full_init.exists():
            init_skipped += 1
            print(f"[SKIP] __init__.py exists: {full_init}")
        else:
            full_init.touch()
            init_created += 1
            print(f"[CREATE] __init__.py: {full_init}")
    
    print(f"\n{'='*50}")
    print(f"Project Structure Setup Complete")
    print(f"Directories created: {created_count}, skipped: {skipped_count}")
    print(f"__init__.py files created: {init_created}, skipped: {init_skipped}")
    print(f"{'='*50}")
    
    # Verify structure by listing all created directories
    print("\nVerifying structure:")
    for dir_path in directories:
        full_path = root / dir_path
        if full_path.exists():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} (MISSING)")
            return False
    
    return True

if __name__ == "__main__":
    success = create_project_structure()
    sys.exit(0 if success else 1)
