"""
Task T001: Initialize project directory structure.
Creates the full directory tree for PROJ-181 and ensures .gitkeep files exist.
"""
import os
import sys
from pathlib import Path

# Define the project root and relative paths based on tasks.md
PROJECT_ROOT = Path(__file__).parent.parent
PROJECT_NAME = "PROJ-181-predicting-species-distribution-shifts-u"
PROJECT_DIR = PROJECT_ROOT / "projects" / PROJECT_NAME

# Define the required subdirectories relative to the project root
SUBDIRS = [
    "data",
    "data/raw",
    "data/processed",
    "data/artifacts",
    "code",
    "code/utils",
    "tests/unit",
    "tests/integration",
    "metrics",
    "reports",
    "logs",
    "state",
    "contracts",
]

def main():
    """Create directory structure and .gitkeep files."""
    print(f"Initializing project structure at: {PROJECT_DIR}")
    
    # Ensure the base project directory exists
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Created base directory: {PROJECT_DIR}")

    # Create subdirectories and .gitkeep files
    created_count = 0
    for subdir in SUBDIRS:
        dir_path = PROJECT_DIR / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        
        gitkeep_path = dir_path / ".gitkeep"
        # Write .gitkeep only if it doesn't exist or is empty, to avoid overwriting
        if not gitkeep_path.exists() or gitkeep_path.stat().st_size == 0:
            gitkeep_path.touch()
            created_count += 1
            print(f"  Created: {dir_path} (and .gitkeep)")
        else:
            print(f"  Exists: {dir_path}")

    print(f"\nDirectory structure initialization complete.")
    print(f"Created {created_count} new .gitkeep files.")
    print(f"Total subdirectories verified: {len(SUBDIRS)}")
    
    # Verification: List the tree structure
    print("\n--- Directory Structure Verification ---")
    for root, dirs, files in os.walk(PROJECT_DIR):
        level = root.replace(str(PROJECT_DIR), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        sub_indent = ' ' * 2 * (level + 1)
        # Show .gitkeep files specifically
        gitkeeps = [f for f in files if f == '.gitkeep']
        for file in gitkeeps:
            print(f'{sub_indent}{file}')
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
