"""
Project Structure Initialization Script.

This script creates the required directory structure for the llmXive
automated science pipeline project as defined in plan.md.
"""
import os
from pathlib import Path

def main():
    """
    Create the project directory structure.
    
    Creates the following directories relative to the project root:
    - code/simulation, code/analysis, code/visualization, code/reporting
    - data/raw, data/processed, data/results
    - tests/unit, tests/integration
    - contracts
    """
    # Determine project root (assuming script is run from project root or code/)
    # We assume the script is run from the project root directory
    project_root = Path.cwd()
    
    # Define the directories to create
    directories = [
        "code/simulation",
        "code/analysis",
        "code/visualization",
        "code/reporting",
        "data/raw",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/integration",
        "contracts"
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
    
    print(f"\nProject structure initialization complete. {created_count} new directories created.")
    
    # Verify structure
    print("\nVerifying structure:")
    for dir_path in directories:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path}")

if __name__ == "__main__":
    main()
