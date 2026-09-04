import os
import sys
from pathlib import Path

def create_structure():
    """
    Create the project directory structure as defined in the implementation plan.
    Creates: code/, tests/, data/, results/, specs/
    And necessary subdirectories: data/raw, data/processed, data/logs, results/figures
    """
    base_dir = Path.cwd()
    
    directories = [
        "code",
        "code/tests",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "results",
        "results/figures",
        "specs",
        "specs/001-sentiment-revenue-lag-analysis",
        "specs/001-sentiment-revenue-lag-analysis/contracts",
    ]
    
    created = []
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create placeholder files to ensure directories are not empty and to provide structure
    placeholder_files = [
        ("data/logs/.gitkeep", "Log files directory"),
        ("data/raw/.gitkeep", "Raw data files directory"),
        ("data/processed/.gitkeep", "Processed data files directory"),
        ("results/figures/.gitkeep", "Generated figures directory"),
        ("specs/001-sentiment-revenue-lag-analysis/contracts/.gitkeep", "Schema contracts directory"),
    ]
    
    for file_path, comment in placeholder_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            with open(full_path, 'w') as f:
                f.write(f"# {comment}\n")
            print(f"Created placeholder file: {full_path}")
    
    print("\nProject structure creation complete.")
    print(f"Directories created: {len(created)}")
    return True

if __name__ == "__main__":
    create_structure()
