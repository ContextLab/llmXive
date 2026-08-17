"""Utility to create the required project directory structure."""

from pathlib import Path
from typing import Iterable, Union


def create_directories(base_path: Union[Path, str] = Path.cwd()) -> None:
    """
    Create the directory tree required for the project.

    Parameters
    ----------
    base_path : Path | str
        Root directory where the ``projects/PROJ-236-exploring-the-influence-of-network-topol``
        hierarchy will be created. By default the current working directory is used.
    """
    root = Path(base_path) / "projects" / "PROJ-236-exploring-the-influence-of-network-topol"
    # List of directories relative to the repository root
    dirs: Iterable[Path] = [
        root / "code" / "utils",
        root / "code" / "tests" / "unit",
        root / "code" / "tests" / "integration",
        root / "data" / "raw",
        root / "data" / "networks",
        root / "data" / "transport",
        root / "data" / "analysis",
        root / "plots",
        root / "state" / "projects",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Entry point for ``python -m code.setup_project_structure``."""
    create_directories()
    print("Project directory structure created.")


if __name__ == "__main__":
    main()
