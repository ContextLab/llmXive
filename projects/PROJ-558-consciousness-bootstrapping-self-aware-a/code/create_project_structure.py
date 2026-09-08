import os
from pathlib import Path

def create_structure(root_dir: str) -> None:
    """
    Creates the directory structure for project PROJ-558.
    
    Structure:
    projects/PROJ-558-consciousness-bootstrapping-self-aware-a/
    ├── data/
    │   ├── raw
    │   └── processed
    ├── code
    ├── tests
    └── artifacts/
        ├── checkpoints
        └── reports
    
    Args:
        root_dir: The root directory where the project folder will be created.
    """
    project_name = "PROJ-558-consciousness-bootstrapping-self-aware-a"
    base_path = Path(root_dir) / "projects" / project_name
    
    # Define subdirectories relative to the base path
    subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/checkpoints",
        "artifacts/reports"
    ]
    
    for subdir in subdirs:
        full_path = base_path / subdir
        full_path.mkdir(parents=True, exist_ok=True)
        # Ensure the directory actually exists (mkdir with exist_ok=True might fail silently in rare cases)
        if not full_path.is_dir():
            raise RuntimeError(f"Failed to create directory: {full_path}")

def main() -> None:
    """Entry point for creating the project structure."""
    # Default to current working directory as root
    root = os.getcwd()
    print(f"Creating project structure in: {root}/projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    create_structure(root)
    print("Directory structure created successfully.")

if __name__ == "__main__":
    main()
