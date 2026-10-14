"""
init_project.py

Script to create the project root directory for PROJ-152-evaluating-the-impact-of-code-generation
with the required sub‑directories: code/, data/, tests/, and docs/.

This script is idempotent: running it multiple times will not raise an error.
"""

import sys
from pathlib import Path

def create_project_structure() -> None:
    """
    Create the project root and sub‑directories under the repository root.

    Expected layout:
    projects/
        PROJ-152-evaluating-the-impact-of-code-generation/
            code/
            data/
            tests/
            docs/
    """
    # Repository root is two levels up from this file:
    #   <repo_root>/code/init_project.py
    repo_root = Path(__file__).resolve().parents[1]  # points to <repo_root>
    project_root = repo_root / "projects" / "PROJ-152-evaluating-the-impact-of-code-generation"

    subdirs = ["code", "data", "tests", "docs"]
    try:
        for sub in subdirs:
            (project_root / sub).mkdir(parents=True, exist_ok=True)
        print(f"Project structure created at: {project_root}")
    except Exception as e:
        print(f"Failed to create project structure: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    create_project_structure()