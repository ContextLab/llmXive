"""
Directory Setup Script for llmXive Project.

This script creates the core directory structure required for the project,
including code/, data/, tests/, and docs/ along with their subdirectories.
"""
import os
from pathlib import Path
import sys

def create_directories():
    """Create all required project directories."""
    # Define the base project root (current directory)
    project_root = Path(".")
    
    # Define the directory structure to create
    directories = [
        # Core directories
        "code",
        "data",
        "tests",
        "docs",
        
        # Data subdirectories
        "data/raw",
        "data/processed",
        
        # Code subdirectories
        "code/data_acquisition",
        "code/feature_extraction",
        "code/analysis",
        "code/utils",
        
        # Test subdirectories
        "tests/unit",
        "tests/integration",
        "tests/contract",
        
        # Docs subdirectories (optional but good practice)
        "docs/api",
        "docs/design",
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            existing_count += 1
    
    print(f"\nDirectory creation complete.")
    print(f"Created: {created_count} directories")
    print(f"Already existing: {existing_count} directories")
    
    return created_count, existing_count

def main():
    """Main entry point for the directory setup script."""
    print("Starting directory setup for llmXive project...")
    print("=" * 50)
    
    try:
        created, existing = create_directories()
        print("=" * 50)
        print("Setup completed successfully!")
        return 0
    except Exception as e:
        print(f"Error during directory creation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
