"""
Script to initialize the project directory structure for the
'Testing the Isotropy of Cosmic Expansion' project.

This script creates the necessary folders as defined in task T001:
- data/raw
- data/processed
- code
- tests/unit
- tests/integration
- tests/contract
- docs
- reports

It also creates placeholder .gitkeep files to ensure the directories
are tracked by version control systems.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to this script's location
# Assuming this script is in code/, we go up one level to the root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# List of directories to create relative to the project root
DIRECTORIES = [
    "data/raw",
    "data/processed",
    "code",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "docs",
    "reports"
]

def create_directories():
    """Create the directory structure and .gitkeep files."""
    created_count = 0
    for dir_path in DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        
        if full_path.exists():
            print(f"Directory exists: {full_path.relative_to(PROJECT_ROOT)}")
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(PROJECT_ROOT)}")
            created_count += 1
        
        # Create a .gitkeep file to ensure the directory is tracked
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"  -> Created .gitkeep in {full_path.relative_to(PROJECT_ROOT)}")

    return created_count

def main():
    print(f"Initializing project structure at: {PROJECT_ROOT}")
    created = create_directories()
    print(f"\nSetup complete. Created {created} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
