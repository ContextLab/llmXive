import os
import sys
from pathlib import Path

def create_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    # Create a .gitkeep file to ensure the directory is tracked by git
    gitkeep = path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("# Keep this directory in version control\n")

def main() -> None:
    """Create the standard project directory structure."""
    root = Path(__file__).resolve().parent.parent
    
    directories = [
        root / "code",
        root / "data",
        root / "data" / "generated",
        root / "data" / "human",
        root / "data" / "processed",
        root / "results",
        root / "figures",
        root / "state",
        root / "tests",
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "tests" / "contract",
    ]
    
    print(f"Creating project structure in: {root}")
    for directory in directories:
        create_directory(directory)
        print(f"  Created: {directory.relative_to(root)}")
    
    print("Project structure creation complete.")
