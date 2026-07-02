"""
Setup script to create the required subdirectory structure for the code module.
This script creates the following directories under the project root:
- code/data_download
- code/manipulation
- code/preprocess
- code/analysis
- code/visualization
- code/utils
- code/pipeline
"""
import os
import sys
from pathlib import Path


def create_code_subdirectories(root_path: Path) -> None:
    """
    Create the required code subdirectories.

    Args:
        root_path: The project root directory path.
    """
    code_dirs = [
        "data_download",
        "manipulation",
        "preprocess",
        "analysis",
        "visualization",
        "utils",
        "pipeline",
    ]

    for dir_name in code_dirs:
        dir_path = root_path / "code" / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create an empty __init__.py to ensure each is a valid Python package
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")
        print(f"Created directory: {dir_path}")


def main() -> None:
    """Main entry point for the script."""
    # Determine project root (assuming script is run from project root or code/)
    # If run as `python code/setup_code_structure.py`, we need to go up one level
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    print(f"Project root detected at: {project_root}")

    # Ensure the 'code' directory exists
    code_root = project_root / "code"
    code_root.mkdir(parents=True, exist_ok=True)

    create_code_subdirectories(project_root)
    print("Code subdirectory setup complete.")


if __name__ == "__main__":
    main()
