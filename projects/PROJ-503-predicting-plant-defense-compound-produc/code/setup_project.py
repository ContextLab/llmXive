import os
import sys
from pathlib import Path

def setup_project_structure(base_path: str) -> None:
    """
    Create the required project directory structure for PROJ-503.
    
    Args:
        base_path: The root path where the project structure should be created.
                   Should be 'projects/PROJ-503-predicting-plant-defense-compound-produc'
    """
    project_root = Path(base_path)
    
    # Define all required directories relative to the project root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/paired",
        "logs",
        "outputs/models",
        "docs",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "code/models"  # Ensure models directory exists for T006
    ]
    
    created_dirs = []
    failed_dirs = []
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
        except OSError as e:
            failed_dirs.append((str(full_path), str(e)))
    
    if failed_dirs:
        print("Failed to create the following directories:")
        for path, error in failed_dirs:
            print(f"  - {path}: {error}")
        sys.exit(1)
    
    print(f"Successfully created {len(created_dirs)} directories under {project_root}")
    for d in sorted(created_dirs):
        print(f"  {d}")

def main():
    """Entry point for running the setup script."""
    # The base path is the project root as defined in the task
    base_path = "projects/PROJ-503-predicting-plant-defense-compound-produc"
    setup_project_structure(base_path)

if __name__ == "__main__":
    main()