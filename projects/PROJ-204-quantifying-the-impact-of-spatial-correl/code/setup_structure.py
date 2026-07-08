import os
from pathlib import Path

__all__ = ["create_project_structure"]

def create_project_structure(base_dir: Path = Path(".")) -> None:
    """
    Create the standard project directory hierarchy.

    The function ensures the existence of the following directories:

    - ``code/``
    - ``data/raw/``
    - ``data/processed/``
    - ``tests/``
    - ``state/``
    - ``docs/``

    Parameters
    ----------
    base_dir: Path, optional
        Base directory where the structure will be created (default current
        directory).
    """
    dirs = [
        base_dir / "code",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "tests",
        base_dir / "state",
        base_dir / "docs",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print("Project structure created.")
