"""Setup script for task T001a.

Creates the required project directory structure:
projects/PROJ-678-comparative-analysis-of-molecular-fingerprints/
    data/raw/
    data/processed/
    code/
    tests/

The ``data/raw`` and ``data/processed`` directories receive a ``.gitkeep``
file so that they are tracked by version control even when empty.
"""
import os
from pathlib import Path
from llmxive_toolkit import get_logger

log = get_logger(__name__)

PROJECT_NAME = "PROJ-678-comparative-analysis-of-molecular-fingerprints"


def _make_tree(root: Path) -> None:
    """Create the directory tree and placeholder ``.gitkeep`` files.

    Parameters
    ----------
    root: Path
        Base path where the project structure will be created.
    """
    subdirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "code",
        root / "tests",
    ]

    for d in subdirs:
        d.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {d}")

        # Add a .gitkeep file to data subfolders so they are not empty in Git.
        if d.name in {"raw", "processed"}:
            gitkeep = d / ".gitkeep"
            gitkeep.touch(exist_ok=True)
            log.info(f"Added .gitkeep to: {gitkeep}")

    # Optionally create an empty __init__.py in the new code folder
    init_file = root / "code" / "__init__.py"
    init_file.touch(exist_ok=True)
    log.info(f"Ensured __init__.py exists at: {init_file}")


def main() -> None:
    """Entry point for the directory‑creation script.

    The script resolves the repository root (two levels up from this file)
    and then creates the required project subtree under ``projects/``.
    """
    # Resolve repository root (the directory containing the ``projects`` folder)
    repo_root = Path(__file__).resolve().parent.parent
    target_root = repo_root / "projects" / PROJECT_NAME

    log.info(f"Creating project structure at: {target_root}")
    _make_tree(target_root)
    log.info("Project directory structure created successfully.")


if __name__ == "__main__":
    main()
