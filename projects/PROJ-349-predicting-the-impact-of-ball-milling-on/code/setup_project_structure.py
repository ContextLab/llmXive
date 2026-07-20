import os
import sys
from pathlib import Path


def setup_directories(root_path: Path = None) -> None:
    """
    Create the standard project directory structure.

    Creates the following directories relative to root_path:
    - src/
    - tests/
    - data/raw/
    - data/processed/
    - data/splits/
    - results/
    - contracts/
    - .github/workflows/

    Each directory will contain a .gitkeep file to ensure
    they are tracked by git even when empty.

    Args:
        root_path: The root directory for the project.
                  Defaults to the current working directory.
    """
    if root_path is None:
        root_path = Path.cwd()
    else:
        root_path = Path(root_path)

    # Define the directory structure to create
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/splits",
        "results",
        "contracts",
        ".github/workflows"
    ]

    print(f"Setting up project structure at: {root_path}")

    for dir_path in directories:
        full_path = root_path / dir_path
        
        # Create directory if it doesn't exist
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {dir_path}")
        else:
            print(f"  Exists:  {dir_path}")
        
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"    Added .gitkeep")

    print("Project structure setup complete.")


if __name__ == "__main__":
    # Allow running as a script
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    setup_directories(root)