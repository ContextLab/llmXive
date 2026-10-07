"""
Directory setup utilities for the llmXive research pipeline.
Creates the required project structure including data directories.
"""
import os
from pathlib import Path


def create_project_structure():
    """
    Creates the full project directory structure required by the pipeline.
    Specifically implements T001a, T001b, and T001c requirements.
    """
    # Base project root (assumed to be run from project root)
    project_root = Path.cwd()

    # Define all required directories based on tasks.md
    directories = [
        # T001a: Code structure
        "code",
        "code/ingestion",
        "code/processing",
        "code/analysis",
        "code/utils",
        "code/tests",
        
        # T001b: Data structure
        "data",
        "data/raw/tng100",
        "data/raw/millennium",
        "data/processed",
        "data/metadata",
        
        # T001c: Output structure
        "outputs",
        "outputs/figures",
        "outputs/reports",
        
        # Additional standard directories (implied by plan.md and other tasks)
        "docs",
        "state",
        "logs",
        "scripts",
        "paper",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1

    return created_count


if __name__ == "__main__":
    count = create_project_structure()
    print(f"Created {count} new directories.")
    print("Project structure ready.")
