"""
Script to initialize the project directory structure as per T001.
"""
import os
from pathlib import Path

def main():
    base_dir = Path(__file__).parent
    project_root = base_dir / "projects" / "PROJ-582-socratic-transformers-dialogue-based-sel" / "code"

    # Define directories to create
    dirs_to_create = [
        "src",
        "src/data",
        "src/train",
        "src/eval",
        "src/analyze",
        "src/utils",
        "tests",
        "tests/contract",
        "tests/integration",
        # Data directories for T004 (created here for verification convenience)
        "data/raw",
        "data/processed",
        "data/results",
    ]

    print(f"Creating project structure in: {project_root}")
    
    for d in dirs_to_create:
        full_path = project_root / d
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {full_path}")

    # Create .gitkeep files for data directories (T004 requirement)
    data_dirs = ["data/raw", "data/processed", "data/results"]
    for d in data_dirs:
        full_path = project_root / d / ".gitkeep"
        full_path.touch()
        print(f"  Created: {full_path}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()