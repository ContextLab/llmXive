"""
Script to initialize the project directory structure for llmXive follow-up.
Creates all required folders for data, code, tests, specs, and state management.
"""
import os
from pathlib import Path

def main():
    # Define the project root based on the task description
    project_root = Path("projects/PROJ-905-llmxive-follow-up-extending-fastcontext")
    
    # Ensure the root exists
    project_root.mkdir(parents=True, exist_ok=True)
    
    # Define the relative paths to create as per T001 requirements
    # Data directories
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/results"
    ]
    
    # Code and test directories
    code_test_dirs = [
        "code",
        "tests/unit",
        "tests/integration"
    ]
    
    # Specs and state directories
    other_dirs = [
        "specs/contracts",
        "state"
    ]
    
    all_dirs = data_dirs + code_test_dirs + other_dirs
    
    created_count = 0
    for rel_path in all_dirs:
        full_path = project_root / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")
    
    print(f"Project structure initialization complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()