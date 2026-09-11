"""
Script to set up the project directory structure for the llmXive pipeline.
Creates necessary directories for data, code modules, tests, and reports.
"""
import os
from pathlib import Path

def create_project_structure():
    """
    Creates the standard directory structure for the project.
    Ensures all required folders exist relative to the project root.
    """
    # Define the root directory (current working directory or project root)
    root = Path(__file__).resolve().parent.parent

    # Define the directory structure to create
    directories = [
        # Data directories
        "data/raw",
        "data/processed",
        
        # Code module directories
        "code/data",
        "code/preprocess",
        "code/analysis",
        "code/modeling",
        "code/validation",
        "code/report",
        "code/utils",
        
        # Testing directory
        "tests",
        
        # State and documentation directories (referenced in T001/T004)
        "state",
        "state/projects",
        "docs",
        
        # Logs directory (referenced in T007)
        "logs",
        
        # Figures directory for output plots
        "figures",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Project structure setup complete. {created_count} new directories created.")
    return created_count

if __name__ == "__main__":
    create_project_structure()
