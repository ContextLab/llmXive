"""
Project initialization script for llmXive automated science pipeline.
Creates the standard directory structure and placeholder files.
"""
import os
from pathlib import Path


def create_project_structure(root_dir: str = ".") -> None:
    """
    Create the standard project directory structure:
    - code/
    - data/raw/
    - data/processed/
    - tests/
    - specs/ (if not exists)
    - state/projects/ (if not exists)

    Creates placeholder __init__.py files in Python directories.
    """
    base = Path(root_dir)

    # Define required directories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "specs",
        "state/projects",
        "figures",
        "docs",
    ]

    created_dirs = []

    for dir_path in directories:
        full_path = base / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    # Create __init__.py files in Python directories
    python_dirs = ["code", "tests"]
    for dir_name in python_dirs:
        init_file = base / dir_name / "__init__.py"
        if not init_file.exists():
            init_file.write_text(
                "# llmXive project package\n"
                "import logging\n"
                "\n"
                "logger = logging.getLogger(__name__)\n"
                "setup_logger = None\n"
            )
            print(f"Created placeholder: {init_file}")
        else:
            # Ensure it has minimal content if empty
            if init_file.stat().st_size == 0:
                init_file.write_text(
                    "# llmXive project package\n"
                    "import logging\n"
                    "\n"
                    "logger = logging.getLogger(__name__)\n"
                    "setup_logger = None\n"
                )
                print(f"Initialized empty __init__.py: {init_file}")

    # Create placeholder .gitkeep in data directories to ensure they are tracked
    data_dirs = ["data/raw", "data/processed", "figures"]
    for dir_name in data_dirs:
        gitkeep = base / dir_name / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Keep this directory in git\n")
            print(f"Created .gitkeep: {gitkeep}")

    print("\nProject structure initialization complete.")
    print(f"Created {len(created_dirs)} directories.")


if __name__ == "__main__":
    create_project_structure()
