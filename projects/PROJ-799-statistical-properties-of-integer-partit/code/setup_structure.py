"""
Project Structure Setup Script.

This script creates the complete directory structure required for the
Statistical Properties of Integer Partitions project (PROJ-799).
"""
import os
import sys
from pathlib import Path

def main():
    """Create the complete project directory hierarchy."""
    # Base project directory
    base_dir = Path("projects/PROJ-799-statistical-properties-of-integer-partit")

    # Define all required subdirectories relative to the project root
    # Note: The prompt specifies paths relative to project root, but since
    # this script runs from the repo root, we construct paths relative to base_dir
    
    directories = [
        # Code infrastructure
        base_dir / "code",
        base_dir / "code" / "utils",
        
        # Data storage
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "schemas",
        
        # Testing infrastructure
        base_dir / "tests",
        base_dir / "tests" / "data",
        
        # Documentation
        base_dir / "docs",
        
        # State management
        base_dir / "state",
        base_dir / "state" / "projects",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    print(f"Project root: {base_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
