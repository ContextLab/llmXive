"""
Project structure initialization script for llmXive.
Creates the required directory hierarchy as per the implementation plan.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the root directory (current working directory or project root)
    root = Path(".")
    
    # Define the required directories relative to the root
    # Based on tasks.md T001 requirements
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/analysis",
        "models",
        "analysis",
        "tests",
        "docs"
    ]
    
    created_count = 0
    existing_count = 0
    
    print("Initializing llmXive project structure...")
    
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            existing_count += 1
    
    print(f"\nProject structure initialization complete.")
    print(f"Created: {created_count} directories")
    print(f"Existing: {existing_count} directories")
    
    # Verify structure
    print("\nVerifying directory structure:")
    all_exist = True
    for dir_path in directories:
        full_path = root / dir_path
        if full_path.exists():
            print(f"  [OK] {full_path}")
        else:
            print(f"  [FAIL] {full_path}")
            all_exist = False
    
    if all_exist:
        print("\n✓ All required directories are present.")
        return 0
    else:
        print("\n✗ Some directories are missing. Initialization failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
