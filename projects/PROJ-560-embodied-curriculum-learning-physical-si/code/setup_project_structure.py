import os
from pathlib import Path

def create_directory(path: str) -> None:
    """Create a directory if it does not exist."""
    dir_path = Path(path)
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    else:
        print(f"Directory already exists: {dir_path}")

def main() -> None:
    """Create the full project directory structure."""
    project_root = Path(__file__).parent.parent

    # Define all required directories relative to project root
    directories = [
        "code/src",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "data/derivation_logs",
        "state/projects/PROJ-560-embodied-curriculum-learning-physical-si"
    ]

    for dir_path in directories:
        create_directory(str(project_root / dir_path))

    print("Project structure setup complete.")

if __name__ == "__main__":
    main()