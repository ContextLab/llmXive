import os
import sys
from pathlib import Path

def create_directories(base_path: Path):
    """
    Create the full project directory structure for PROJ-756.
    Ensures all required subdirectories exist.
    """
    # Define the project root relative to the code directory or current working directory
    # The task specifies: projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/
    project_root = base_path / "projects" / "PROJ-756-assessing-dataset-imbalance-effects-on-m"
    
    # Define required subdirectories
    subdirs = [
        "data",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "code",
        "tests",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "artifacts",
        "results",
        "results/shap_analysis",
        "state",
        "logs",
        "logs/archive"
    ]
    
    created_dirs = []
    for subdir in subdirs:
        dir_path = project_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(dir_path.relative_to(base_path)))
    
    return created_dirs

def main():
    """
    Entry point to create the project directory structure.
    """
    # Determine base path (current working directory)
    base_path = Path.cwd()
    
    print(f"Creating project structure in: {base_path}")
    
    try:
        created = create_directories(base_path)
        print("Successfully created directories:")
        for d in created:
            print(f"  - {d}")
        print("Project structure setup complete.")
        return 0
    except Exception as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())