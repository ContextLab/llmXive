"""Setup script to establish the required project directory layout.

This script creates the standard folder hierarchy for the project
``PROJ-050-the-effect-of-priming-on-prosocial-behav`` under the top‑level
``projects/`` directory. It is idempotent – running it multiple times will
not raise errors and will simply ensure the directories exist.

Execution of this script satisfies task T001.
"""
import sys
from pathlib import Path

def main() -> None:
    # Resolve the repository root (one level above the ``code`` folder)
    repo_root = Path(__file__).resolve().parents[1]

    # Target project directory
    proj_dir = repo_root / "projects" / "PROJ-050-the-effect-of-priming-on-prosocial-behav"

    # List of sub‑directories to create
    subdirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/validation",
        "data/results",
        "docs",
        "specs",
        "tests/unit",
        "tests/integration",
        "results",
        "figures",
        "paper",
        "logs",
    ]

    # Create each directory (parents=True allows nested creation)
    for sub in subdirs:
        dir_path = proj_dir / sub
        dir_path.mkdir(parents=True, exist_ok=True)

    print(f"Project layout created at: {proj_dir}", file=sys.stdout)

if __name__ == "__main__":
    main()
