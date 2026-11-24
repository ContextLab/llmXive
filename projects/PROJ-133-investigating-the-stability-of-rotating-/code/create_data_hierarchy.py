"""Utility script to create the required data sub‑directories.

The script is executed once during project scaffolding to ensure that
``data/raw``, ``data/processed`` and ``data/aggregated`` exist, each
containing a ``.gitkeep`` placeholder file.  All public objects have
docstrings.
"""

from pathlib import Path

from llmxive_toolkit import paths

def _ensure_dir_with_placeholder(dir_path: Path) -> None:
    """Ensure *dir_path* exists and contains a ``.gitkeep`` file.

    Parameters
    ----------
    dir_path : pathlib.Path
        Directory to create (parents are created as needed).
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    placeholder = dir_path / ".gitkeep"
    if not placeholder.exists():
        placeholder.touch()

def main() -> None:
    """Create the three top‑level data sub‑folders.

    The function creates ``data/raw``, ``data/processed`` and
    ``data/aggregated`` inside the project root and writes a ``.gitkeep``
    file into each to keep the directories under version control.
    """
    for sub in ("raw", "processed", "aggregated"):
        _ensure_dir_with_placeholder(paths.data(sub))
