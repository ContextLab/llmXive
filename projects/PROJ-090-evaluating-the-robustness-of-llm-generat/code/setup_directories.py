"""
Directory structure initialization for the LLM Robustness Evaluation project.

This script creates the required directory hierarchy under the project root.
It ensures all necessary folders for code, data, tests, and logs exist.
"""
import os
from pathlib import Path


def create_directories():
    """
    Create the complete directory structure for the project.
    
    Creates:
    - code/, code/data/, code/model/, code/analysis/, code/utils/
    - data/, data/raw/, data/processed/, data/logs/
    - tests/, tests/unit/, tests/contract/
    
    Returns:
        bool: True if all directories were created successfully.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    # Define directory structures
    directories = [
        # Code structure
        "code",
        "code/data",
        "code/model",
        "code/analysis",
        "code/utils",
        
        # Data structure
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        
        # Tests structure
        "tests",
        "tests/unit",
        "tests/contract",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {full_path}")
        else:
            print(f"Exists: {full_path}")
    
    print(f"\nDirectory initialization complete. Created {created_count} new directories.")
    return True


if __name__ == "__main__":
    create_directories()