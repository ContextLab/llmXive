#!/usr/bin/env python3
"""
Setup script for the PROJ-448-quantifying-grain-boundary-segregation project.

This script initializes the project directory structure required for the
automated science pipeline. It creates all necessary directories for code,
data, tests, and research artifacts if they do not already exist.

Usage:
    python scripts/setup_project.py
"""

import os
import sys
from pathlib import Path


def create_directories():
    """
    Create the project directory structure.

    Creates the following directories relative to the project root:
    - projects/PROJ-448-quantifying-grain-boundary-segregation/
    - code/
    - data/
    - data/figures/
    - data/processed/
    - tests/
    - research/

    Returns:
        list[str]: A list of created directory paths (relative to root).
    """
    # Define the project root (parent of 'scripts' directory)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define the required directory structure relative to the project root
    # Note: The task specifies creating 'projects/PROJ-448-...' as the root
    # but also lists 'code/', 'data/', etc. which are typically inside the project.
    # Based on the task description "Create ... explicit directory definitions for ...",
    # we will create the specific project folder and then the standard subfolders
    # inside it or at the root as implied by the list.
    #
    # Re-reading the task: "Create ... definitions for `projects/PROJ-448-...`, `code/`, `data/`..."
    # This implies `code/`, `data/` are siblings to the project folder OR inside it.
    # However, standard practice for this pipeline (and the task's later references like
    # "projects/PROJ-448-.../code/") suggests the project folder is the root of the work.
    #
    # Let's interpret the task literally:
    # 1. Create `projects/PROJ-448-quantifying-grain-boundary-segregation/`
    # 2. Create `code/`, `data/`, `tests/`, `research/` inside that project folder.
    #
    # The task lists: `projects/PROJ-448-quantifying-grain-boundary-segregation/`, `code/`, `data/`, `tests/`, `research/`, `data/figures/`, `data/processed/`.
    # If these were all at the repo root, the project name wouldn't be a container.
    # The most logical structure is:
    # projects/
    #   PROJ-448-quantifying-grain-boundary-segregation/
    #     code/
    #     data/
    #       figures/
    #       processed/
    #     tests/
    #     research/
    #
    # We will implement this structure.

    base_path = project_root / "projects" / "PROJ-448-quantifying-grain-boundary-segregation"

    directories = [
        base_path,
        base_path / "code",
        base_path / "data",
        base_path / "data" / "figures",
        base_path / "data" / "processed",
        base_path / "tests",
        base_path / "research",
    ]

    created = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory.relative_to(project_root)))
            print(f"Created directory: {directory.relative_to(project_root)}")
        else:
            print(f"Directory already exists: {directory.relative_to(project_root)}")

    # Create __init__.py files to ensure these are recognized as Python packages
    # where applicable (code, tests)
    init_files = [
        base_path / "code" / "__init__.py",
        base_path / "tests" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            created.append(str(init_file.relative_to(project_root)))
            print(f"Created file: {init_file.relative_to(project_root)}")
        else:
            print(f"File already exists: {init_file.relative_to(project_root)}")

    return created


def main():
    """Main entry point for the setup script."""
    print("Starting project setup for PROJ-448-quantifying-grain-boundary-segregation...")
    created_items = create_directories()
    print(f"\nSetup complete. Created {len(created_items)} items.")
    return 0


if __name__ == "__main__":
    sys.exit(main())