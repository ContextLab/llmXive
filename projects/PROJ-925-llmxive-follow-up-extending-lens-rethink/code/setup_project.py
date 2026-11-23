"""
Project structure creation script for llmXive follow-up.
Executes the directory hierarchy creation as specified in T001b.
"""
import os
import sys
from pathlib import Path


def create_structure():
    """
    Creates the required directory structure for the project.
    
    Creates sibling directories at the project root:
    - data/raw
    - data/processed
    - code
    - code/tests
    - code/utils
    - code/models
    - docs
    
    Note: data/ and code/ are SIBLINGS, not nested.
    """
    # Determine project root (parent of 'code' directory)
    # We assume this script is run from the project root or code/ directory
    current_file = Path(__file__).resolve()
    if current_file.name == '__main__':
        project_root = Path.cwd()
    else:
        # If run as module, assume script is in code/
        project_root = current_file.parent.parent
    
    # Define relative paths relative to project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/tests",
        "code/utils",
        "code/models",
        "docs",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nStructure creation complete. Created {created_count} new directories.")
    return True


def main():
    """Main entry point for the script."""
    try:
        create_structure()
        print("SUCCESS: Project structure created successfully.")
        return 0
    except Exception as e:
        print(f"ERROR: Failed to create project structure: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
