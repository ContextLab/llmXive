"""
Script to initialize the project directory structure for llmXive Follow-up: Extending ProRL for Zero-Shot Proactive Recommendation.

This script creates the required directories and empty __init__.py files
as specified in task T001.
"""
import os
from pathlib import Path

def create_project_structure():
    """Create the project directory structure and __init__.py files."""
    # Define the directories to create relative to the project root
    directories = [
        "src",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "results"
    ]
    
    # Create each directory
    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    
    # Create __init__.py files in src and tests
    init_files = [
        "src/__init__.py",
        "tests/__init__.py"
    ]
    
    for init_file in init_files:
        path = Path(init_file)
        # Create empty file (touch)
        path.touch()
        print(f"Created empty file: {path}")
    
    print("\nProject structure initialized successfully.")

if __name__ == "__main__":
    create_project_structure()