import os
import sys
from pathlib import Path

def create_structure(root_dir: Path) -> None:
    """
    Create the standard project directory structure.
    This is an alias/helper for setup_directories to ensure consistency.
    """
    # Re-use the logic from setup_directories to avoid duplication
    # In a real scenario, we might import from setup_directories,
    # but to keep this file self-contained as per the API surface provided:
    
    directories = [
        "data/raw",
        "data/processed",
        "data/residualized",
        "data/models/lofo_models",
        "artifacts",
        "state",
        "code/src/data",
        "code/src/models",
        "code/src/utils",
        "code/tests/unit",
        "code/tests/integration",
        "docs",
        "figures",
    ]

    for dir_path in directories:
        full_path = root_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure empty directories are tracked
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
        
def main() -> None:
    """
    Entry point.
    """
    root_dir = Path(__file__).resolve().parent.parent
    create_structure(root_dir)
    print("Project structure initialized.")

if __name__ == "__main__":
    main()
