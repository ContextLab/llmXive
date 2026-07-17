"""
Project Structure Initialization Script.

This script creates the required directory structure for the llmXive project
as specified in the implementation plan.

Creates:
- code/data, code/analysis, code/tests
- data/raw, data/processed
- docs/output
"""
import os
import sys
from pathlib import Path


def main():
    """Create the project directory structure."""
    # Define the project root (parent of this script's directory)
    # We assume this script is in the 'code' directory
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        project_root / "code" / "data",
        project_root / "code" / "analysis",
        project_root / "code" / "tests",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "docs" / "output",
        project_root / "logs",  # Needed for T005 logging
    ]
    
    created = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory.relative_to(project_root)))
            print(f"Created directory: {directory.relative_to(project_root)}")
        else:
            print(f"Directory already exists: {directory.relative_to(project_root)}")
    
    if created:
        print(f"\nSuccessfully created {len(created)} directories.")
    else:
        print("\nNo new directories created. All directories already exist.")
        
    return 0


if __name__ == "__main__":
    sys.exit(main())