"""
Script to create the project directory structure for llmXive PROJ-409.

This script implements Task T001 by creating all required directories
under the project root as specified in the implementation plan.
"""
import os
import sys
from pathlib import Path

def create_directory_structure():
    """
    Creates the full project directory structure required for the pipeline.
    
    Directories created:
    - code/, code/extraction/, code/inference/, code/analysis/, code/utils/
    - data/raw/, data/extracted/, data/aggregated/, data/results/, data/models/
    - tests/unit/, tests/integration/
    """
    # Define all required directories relative to the project root
    # We assume the script is run from the project root or the code directory
    # The base path is the parent of this file's location (project root)
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "code/extraction",
        "code/inference",
        "code/analysis",
        "code/utils",
        "data/raw",
        "data/extracted",
        "data/aggregated",
        "data/results",
        "data/models",
        "tests/unit",
        "tests/integration"
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Creating project structure in: {base_path}")
    
    for dir_path in directories:
        full_path = base_path / dir_path
        if full_path.exists():
            existing_count += 1
            print(f"  [SKIP] {dir_path} (already exists)")
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"  [CREATE] {dir_path}")
    
    print(f"\nSummary: {created_count} directories created, {existing_count} already existed.")
    return created_count == len(directories) or all((base_path / d).exists() for d in directories)

def main():
    """Entry point for the script."""
    success = create_directory_structure()
    if success:
        print("\nProject structure verification: PASSED")
        sys.exit(0)
    else:
        print("\nProject structure verification: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
