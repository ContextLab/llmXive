"""
Script to create the project structure for llmXive research pipeline.
Creates the following directories:
- code/
- data/
- results/
- state/
- tests/
- specs/
- figures/
"""
import os
from pathlib import Path

def create_project_structure():
    """Create the standard project directory structure."""
    base_dirs = [
        "code",
        "code/utils",
        "code/data",
        "code/models",
        "code/benchmark",
        "data",
        "data/raw",
        "data/processed",
        "results",
        "state",
        "tests",
        "tests/unit",
        "tests/integration",
        "specs",
        "figures"
    ]

    current_dir = Path.cwd()
    
    for dir_path in base_dirs:
        full_path = current_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create __init__.py files for Python packages
        if dir_path.startswith("code") or dir_path.startswith("tests"):
          init_file = full_path / "__init__.py"
          if not init_file.exists():
              init_file.touch()
          # Add docstring to __init__.py for better package structure
          if dir_path == "code":
              init_file.write_text('"""llmXive research pipeline code."""\n')
          elif dir_path == "tests":
              init_file.write_text('"""Test suite for llmXive research pipeline."""\n')
          elif dir_path.startswith("code/"):
              init_file.write_text(f'"""{dir_path} module."""\n')
          elif dir_path.startswith("tests/"):
              init_file.write_text(f'"""{dir_path} test module."""\n')

    print("Project structure created successfully:")
    for dir_path in base_dirs:
        print(f"  - {dir_path}/")

if __name__ == "__main__":
    create_project_structure()