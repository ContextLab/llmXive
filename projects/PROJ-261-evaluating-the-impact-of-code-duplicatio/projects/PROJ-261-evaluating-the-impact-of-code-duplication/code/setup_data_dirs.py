"""Setup data directory structure for the project.

This script creates the following sub‑directories under the project's
``data`` folder:

- ``raw``       – for raw downloaded datasets
- ``processed`` – for intermediate CSV/JSON files produced by the pipeline
- ``analysis``  – for final analysis artefacts (e.g., correlation results,
  visualisation figures)

The script is idempotent; running it multiple times will not raise an error
if the directories already exist.
"""

from pathlib import Path
import sys


def _project_root() -> Path:
    """Return the absolute path to the project root (the directory that contains
    the ``code`` and ``data`` folders).

    The script lives in ``.../code/setup_data_dirs.py``; the project root is its
    parent directory.
    """
    return Path(__file__).resolve().parents[1]


def create_data_subdirs(root: Path) -> None:
    """Create the required ``data`` sub‑directories.

    Args:
        root: Path to the project root.
    """
    data_dir = root / "data"
    subdirs = ["raw", "processed", "analysis"]
    for sub in subdirs:
        sub_path = data_dir / sub
        sub_path.mkdir(parents=True, exist_ok=True)
        # Ensure the directory is tracked by git even if empty.
        gitkeep = sub_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()


def main(argv: list[str] | None = None) -> int:
    """Entry point for the script.

    Returns:
        Exit code (0 for success, non‑zero for failure).
    """
    try:
        root = _project_root()
        create_data_subdirs(root)
        print(f"Data directories created under: {root / 'data'}")
        return 0
    except Exception as exc:  # pragma: no cover – defensive
        print(f"Failed to create data directories: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())