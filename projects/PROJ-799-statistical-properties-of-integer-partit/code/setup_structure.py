"""
Setup script to create the project directory structure for PROJ-799.
This script ensures all required directories exist under the project root.
"""
import os
import sys

def main():
    """Create the required directory structure for the project."""
    # Determine project root relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Define the relative paths to create
    relative_paths = [
        "code",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/schemas",
        "tests",
        "tests/data",
        "docs",
        "state/projects"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for rel_path in relative_paths:
        full_path = os.path.join(project_root, rel_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Created directory: {rel_path}")
            created_count += 1
        else:
            skipped_count += 1
    
    print(f"\nDirectory setup complete.")
    print(f"  Created: {created_count} directories")
    print(f"  Skipped (already exist): {skipped_count} directories")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
