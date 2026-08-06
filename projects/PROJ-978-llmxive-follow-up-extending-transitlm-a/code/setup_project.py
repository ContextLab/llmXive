"""
Project Setup Script for llmXive follow-up: extending TransitLM.

This script creates the required directory structure for the project
as specified in the implementation plan.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the project root (current directory)
    project_root = Path(".")
    
    # Define required directories relative to project root
    required_dirs = [
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
    
    print("Setting up llmXive project structure...")
    print(f"Project root: {project_root.absolute()}")
    print("-" * 50)
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        
        if full_path.exists():
            print(f"[SKIP] Directory already exists: {dir_path}")
            existing_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"[CREATE] {dir_path}")
            created_count += 1
    
    print("-" * 50)
    print(f"Setup complete. Created: {created_count}, Existing: {existing_count}")
    
    # Verify all directories exist
    all_exist = all((project_root / d).exists() for d in required_dirs)
    
    if all_exist:
        print("\n✓ All required directories are present.")
        print("\nDirectory structure:")
        for dir_path in sorted(required_dirs):
            full_path = project_root / dir_path
            print(f"  {full_path}/")
        return 0
    else:
        print("\n✗ Some directories failed to create.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
