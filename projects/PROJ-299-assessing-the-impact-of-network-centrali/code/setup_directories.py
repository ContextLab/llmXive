"""
Directory Structure Setup for llmXive Project.

This script creates the required directory structure for the project,
including data/raw, data/processed, data/analysis, and outputs directories.
It also generates a .gitignore file with rules for large files.
"""
import os
import sys
from pathlib import Path


def ensure_directory_structure(root_dir: Path) -> None:
    """
    Create the required directory structure relative to the project root.

    Args:
        root_dir: The project root directory path.
    """
    # Define required directories relative to root
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/analysis",
        "outputs",
        "outputs/viz",
        "outputs/reports",
        "logs",
        "code/download",
        "code/preprocess",
        "code/centrality",
        "code/analysis",
        "code/viz",
        "code/config",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "docs",
        "specs",
    ]

    for dir_path in required_dirs:
        full_path = root_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {full_path}")


def create_gitignore(root_dir: Path) -> None:
    """
    Create a .gitignore file with rules for large files and project artifacts.

    Args:
        root_dir: The project root directory path.
    """
    gitignore_path = root_dir / ".gitignore"

    # Content for .gitignore
    gitignore_content = """
    # Python
    __pycache__/
    *.py[cod]
    *$py.class
    *.so
    .Python
    build/
    develop-eggs/
    dist/
    downloads/
    eggs/
    .eggs/
    lib/
    lib64/
    parts/
    sdist/
    var/
    wheels/
    *.egg-info/
    .installed.cfg
    *.egg

    # Virtual Environments
    venv/
    ENV/
    .env

    # IDE
    .idea/
    .vscode/
    *.swp
    *.swo
    *~

    # Data Files (Large)
    data/raw/*.nii
    data/raw/*.nii.gz
    data/raw/*.csv
    data/processed/*.nii
    data/processed/*.nii.gz
    data/analysis/*.csv
    data/analysis/*.json
    data/analysis/*.parquet
    data/analysis/*.pkl

    # Outputs
    outputs/*.pdf
    outputs/*.png
    outputs/*.jpg
    outputs/*.svg
    outputs/viz/*
    outputs/reports/*

    # Logs
    logs/*.log

    # OS
    .DS_Store
    Thumbs.db

    # Jupyter
    .ipynb_checkpoints

    # Temporary files
    *.tmp
    *.bak
    """

    # Write the .gitignore file
    with open(gitignore_path, "w", encoding="utf-8") as f:
        f.write(gitignore_content.strip())
        f.write("\n")

    print(f"Created/Updated: {gitignore_path}")


def main() -> None:
    """Main entry point for directory setup."""
    # Determine project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    # Assuming this script is at code/setup_directories.py
    project_root = current_file.parent.parent

    print(f"Project Root: {project_root}")
    print("Setting up directory structure...")

    ensure_directory_structure(project_root)
    create_gitignore(project_root)

    print("Directory setup complete.")


if __name__ == "__main__":
    main()
