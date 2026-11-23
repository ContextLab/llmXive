"""
Project scaffolding utility.

This module provides a function to create the required project directory
layout for the temporal discounting study. The function is idempotent:
it will create any missing directories and place a ``.gitkeep`` placeholder
file in each to ensure the directories are tracked by version control.
"""

import os
from pathlib import Path

# The config module provides a helper to locate the repository root.
# It is part of the existing project API.
from config import get_project_root

def create_project_structure() -> None:
    """
    Create the required sub‑folders for the project.

    The layout is:
        projects/PROJ-196-the-role-of-temporal-discounting-in-proc/
            data/
                raw/
                processed/
            code/
            tests/
            docs/

    If a directory already exists the call is a no‑op. After creating each
    directory a ``.gitkeep`` file is written (if not present) so that the
    empty folders are retained in the repository.
    """
    # Base directory for the specific project
    base_dir = (
        get_project_root()
        / "projects"
        / "PROJ-196-the-role-of-temporal-discounting-in-proc"
    )

    # Sub‑directories to ensure
    subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "docs",
    ]

    for sub in subdirs:
        dir_path = base_dir / sub
        dir_path.mkdir(parents=True, exist_ok=True)

        # Ensure a .gitkeep placeholder exists so the folder is not empty.
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text(
                "# This file ensures the directory is tracked by git.\n"
            )

# When the module is executed as a script, run the scaffolding function.
if __name__ == "__main__":
    create_project_structure()
    print(
        f"Project layout created under {get_project_root() / 'projects' / 'PROJ-196-the-role-of-temporal-discounting-in-proc'}"
    )