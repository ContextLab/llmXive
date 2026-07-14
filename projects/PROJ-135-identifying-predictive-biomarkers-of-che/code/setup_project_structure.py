import os
import sys
from pathlib import Path

def create_structure():
    """Creates the required project directory structure."""
    # Define the root (assuming script is in code/ or root)
    if Path.cwd().name == "code":
        root = Path.cwd().parent
    else:
        root = Path.cwd()

    dirs = [
        "src",
        "data/raw",
        "data/processed",
        "results",
        "results/meta_analysis",
        "tests",
        "specs/001-chemo-biomarker-discovery/contracts",
        "state"
    ]

    for d in dirs:
        path = root / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {path}")

    # Create __init__.py in src and tests
    (root / "src" / "__init__.py").touch()
    (root / "tests" / "__init__.py").touch()
    (root / "tests" / "contract" / "__init__.py").touch()
    (root / "tests" / "integration" / "__init__.py").touch()
    (root / "tests" / "unit" / "__init__.py").touch()

    print("Project structure created successfully.")

if __name__ == "__main__":
    create_structure()