import os
from pathlib import Path

def create_directory_structure():
    """
    Creates the project directory structure as per the implementation plan.
    Directories created:
    - src/ (source code)
    - tests/ (test suite)
    - data/ (raw and processed data)
    - results/ (experiment outputs, logs, plots)
    - specs/ (feature specifications and design docs)
    - data/raw (subdirectory for raw data)
    - data/processed (subdirectory for processed data)
    - results/opd (subdirectory for OPD baseline results)
    - results/low_rank_rl (subdirectory for Low-Rank RL results)
    - results/analysis (subdirectory for analysis reports)
    """
    project_root = Path(__file__).parent.parent
    
    # Define the directories to create
    directories = [
        "src",
        "tests",
        "data",
        "results",
        "specs",
        "data/raw",
        "data/processed",
        "results/opd",
        "results/low_rank_rl",
        "results/analysis",
        "results/figures",
        "src/utils",
        "src/data",
        "src/models",
        "src/training",
        "src/analysis",
        "src/cli",
        "tests/unit",
        "tests/integration",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    
    # Create .gitkeep files in empty directories to ensure they are tracked by git
    for dir_path in directories:
        full_path = project_root / dir_path
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {full_path}")

if __name__ == "__main__":
    create_directory_structure()
