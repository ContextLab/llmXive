"""
Script to initialize the project directory structure.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the standard project directories: code/, data/, tests/, specs/, results/, assets/, docs/.
    """
    project_root = Path(__file__).parent.parent
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "specs",
        "results",
        "assets/templates",
        "docs",
        "src/utils",
        "src/data",
        "src/scaffolding",
        "src/scoring",
        "src/agents",
        "src/analysis",
        "src/cli",
        "contracts"
    ]

    for dir_name in directories:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create __init__.py in Python source directories
        if dir_name.startswith("src") or dir_name == "code":
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()

    print(f"Created {len(directories)} directories under {project_root}")
    return True

if __name__ == "__main__":
    create_directories()