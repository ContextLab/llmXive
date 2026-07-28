import os
import sys
from pathlib import Path

def setup_directories(base_path: Path) -> None:
    """
    Creates the required project directory structure.
    This is a duplicate of the logic in setup_project_structure.py to ensure
    backward compatibility if other scripts import this specific module name.
    """
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

    for dir_name in directories:
        full_path = base_path / dir_name
        full_path.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base = Path(sys.argv[1])
    else:
        base = Path.cwd()
    setup_directories(base)
    print(f"Directories created in: {base}")