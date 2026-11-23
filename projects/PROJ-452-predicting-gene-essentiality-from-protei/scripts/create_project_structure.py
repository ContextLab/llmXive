"""
Script to create the project directory structure for the llmXive pipeline.
Creates: code/, data/, results/, tests/, and necessary subdirectories.
"""
import os
from pathlib import Path

def create_project_structure():
    """Create the standard project directories."""
    root = Path.cwd()
    
    # Define the required directories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "results/correlations",
        "results/null_distribution/label_permutation",
        "results/null_distribution/rewired_graphs",
        "results/null_distribution/rewired_correlations",
        "results/pgls",
        "results/sensitivity",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs",
        "state"
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
    
    # Create .gitkeep files to ensure directories are tracked in git
    gitkeep_path = root / "scripts" / ".gitkeep"
    if not gitkeep_path.parent.exists():
        gitkeep_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add .gitkeep to each root level directory if not present
    for dir_name in ["code", "data", "results", "tests", "specs", "state"]:
        keep_file = root / dir_name / ".gitkeep"
        if not keep_file.exists():
            keep_file.touch()
            print(f"Created .gitkeep in: {keep_file}")
    
    print(f"\nProject structure initialization complete. Created {created_count} new directories.")

if __name__ == "__main__":
    create_project_structure()