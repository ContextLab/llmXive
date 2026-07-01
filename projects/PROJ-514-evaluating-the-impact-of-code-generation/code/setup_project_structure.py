import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure as defined in tasks.md T001.
    This script ensures all required folders for the llmXive pipeline exist.
    """
    # Define the relative paths to be created
    # Using a list of relative paths to ensure consistency
    directories = [
        "code/01_data_collection",
        "code/02_static_analysis",
        "code/03_statistical_analysis",
        "code/04_reporting",
        "code/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw/human_samples",
        "data/raw/llm_samples",
        "data/intermediate",
        "data/processed",
        "reports",
        "specs/001-code-smell-comparison"
    ]

    # Get the project root (assuming this script is run from the root or code/)
    # We resolve the path relative to the script's location to be safe, 
    # but typically these commands are run from the project root.
    # If running from 'code/', we need to go up one level.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent if script_path.name == 'setup_project_structure.py' else script_path.parent
    
    # If the script is in 'code/', project_root is the repo root.
    # If the script is in root (unlikely based on task description), project_root is root.
    # Let's assume standard layout: script is in code/, so we go up.
    # However, the task says "relative to project root". 
    # Let's assume the current working directory is the project root when this is executed.
    cwd = Path.cwd()
    
    created_count = 0
    for dir_name in directories:
        target_path = cwd / dir_name
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        except Exception as e:
            print(f"Error creating directory {target_path}: {e}")
            return 1

    print(f"Successfully created {created_count} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())