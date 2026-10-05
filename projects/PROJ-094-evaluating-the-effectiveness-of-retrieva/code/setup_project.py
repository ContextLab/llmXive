import os
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in T001a.
    Creates src/data, src/models, src/analysis, src/cli, src/lib,
    data/raw, data/processed, results, tests/unit, tests/integration, tests/contract.
    """
    project_root = Path(__file__).parent
    
    # Define the directories to create relative to the project root
    directories = [
        "src/data",
        "src/models",
        "src/analysis",
        "src/cli",
        "src/lib",
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "tests/integration",
        "tests/contract"
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
    
    print(f"Directory setup complete. Created {created_count} new directories.")
    return created_count

if __name__ == "__main__":
    create_directories()
