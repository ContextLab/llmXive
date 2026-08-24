import os
import sys
from pathlib import Path
from typing import List

def get_project_root() -> Path:
    """Return the project root directory."""
    # Assume the script is run from the project root or code/ directory
    current = Path.cwd()
    if current.name == "code":
        return current.parent
    return current

def create_directory_structure(root: Path) -> None:
    """Create the standard project directories: code/, tests/, data/."""
    dirs = [
        root / "code",
        root / "tests",
        root / "data",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Created directory: {d}")

def main() -> None:
    """Entry point for the project structure setup."""
    root = get_project_root()
    print(f"Project root detected at: {root}")
    create_directory_structure(root)
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
