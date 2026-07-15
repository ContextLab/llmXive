"""
Project Setup Script for llmXive - Evaluating the Impact of Code Generation Models on Code Vulnerability Density

This script initializes the project directory structure as per the implementation plan.
It creates the necessary folders for code, data, results, state, and tests.
"""

import os
import sys
from pathlib import Path

def main():
    """
    Create the standard project directory structure.
    
    Directories created:
    - code/: Source code modules
    - data/: Raw and processed data
    - results/: Final reports and visualizations
    - state/: Artifact hashes and pipeline state
    - tests/: Unit and integration tests
    """
    # Define the project root (current directory)
    project_root = Path(".")
    
    # Define the required directories
    directories = [
        "code",
        "data/raw",
        "data/generated",
        "data/processed",
        "results",
        "state",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs",
        "docs",
        "config"
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Initializing project structure at: {project_root.absolute()}")
    
    for dir_path in directories:
        full_path = project_root / dir_path
        
        if full_path.exists():
            print(f"  [SKIP] {dir_path} already exists.")
            skipped_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATE] {dir_path}")
            created_count += 1
    
    print(f"\nSetup complete. Created {created_count} directories, skipped {skipped_count}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())