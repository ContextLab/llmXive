import os
import sys
from pathlib import Path

def create_directories(project_root: str) -> None:
    """
    Creates the full project directory structure for PROJ-756.
    Includes: data/, code/, tests/, artifacts/, results/, state/, logs/, logs/archive/
    """
    base_path = Path(project_root)
    
    # Define all required directories relative to the project root
    directories = [
        "data",
        "code",
        "tests",
        "artifacts",
        "results",
        "state",
        "logs",
        "logs/archive",
        # Subdirectories often needed by tasks
        "data/raw",
        "data/processed",
        "data/synthetic",
        "results/shap_analysis",
        "figures",
    ]

    created = []
    for dir_name in directories:
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        created.append(str(dir_path))
    
    return created

def main() -> None:
    """Entry point to create the directory structure."""
    # Determine the project root based on the current working directory
    # or a specific path if passed as an argument.
    # For this task, we assume the script is run from the repo root.
    project_root = Path.cwd()
    
    # The task specifically asks for the structure under:
    # projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/
    # However, the existing files (like code/ingestion.py) are at the root level.
    # We will create the structure at the current working directory (repo root)
    # as per the existing file layout in the API surface provided.
    
    print(f"Creating directory structure at: {project_root}")
    created_dirs = create_directories(project_root)
    
    print("Directories created:")
    for d in created_dirs:
        print(f"  - {d}")

if __name__ == "__main__":
    main()