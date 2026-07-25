import os
import sys
from pathlib import Path

def ensure_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """Create the required project directory structure for PROJ-967."""
    project_root = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")
    
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "results",
    ]

    print(f"Ensuring project structure at: {project_root.absolute()}")
    for directory in directories:
        ensure_directory(directory)
    
    print("Project directory structure creation complete.")

if __name__ == "__main__":
    main()
