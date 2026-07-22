"""
Script to create the project directory structure for llmXive.
Executes the required mkdir commands to establish the baseline file tree.
"""
import os
from pathlib import Path

def create_project_structure():
    """
    Creates the exact directory tree defined in the plan.md structure section.
    Directories created:
    - src/{config,data,models,analysis,utils}
    - tests
    - data/{raw,processed,results}
    - specs/001-gene-regulation/contracts
    - docs
    """
    base_path = Path(__file__).resolve().parent.parent
    
    # Define relative paths based on the task requirement
    # The task asks for paths relative to project root, which is parent of 'scripts'
    # However, the task description implies running this from root or creating relative to root.
    # We will create them relative to the project root (parent of 'scripts' if this is in code/scripts)
    # But standard convention for these tasks is often relative to current working directory or root.
    # Let's assume we are creating these relative to the project root.
    
    # Based on the task: `mkdir -p src/...`
    # We will create these relative to the current working directory (assuming script runs from root)
    # or relative to the script's parent if we want to be safe.
    # The prompt says "All artifact paths are relative to the project root".
    # We will create them relative to the current working directory to match the shell command behavior.
    
    directories = [
        "src/config",
        "src/data",
        "src/models",
        "src/analysis",
        "src/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "specs/001-gene-regulation/contracts",
        "docs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = Path(dir_path)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")
    
    # Verify structure
    print("\nVerifying structure:")
    for dir_path in directories:
        status = "EXISTS" if Path(dir_path).exists() else "MISSING"
        print(f"  [{status}] {dir_path}")

if __name__ == "__main__":
    create_project_structure()
