"""
Utility to ensure the required project directory layout exists.
This implements Task T001.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import List, Optional

def _project_root() -> Path:
    """
    Return the absolute path to the repository root.
    The repository root is assumed to be the parent of the ``code``
    directory that contains this file.
    """
    return Path(__file__).resolve().parent.parent

# The canonical list of required directories relative to the project root.
_REQUIRED_DIRS = [
    "code/src/config",
    "code/src/extraction",
    "code/src/detection",
    "code/src/inference",
    "code/src/analysis",
    "code/src/reporting",
    "code/src/pipeline",
    "code/src/cli",
    "code/tests/unit",
    "code/tests/integration",
    "code/tests/contract",
    "code/data/raw",
    "code/data/annotations",
    "code/data/derived",
    "code/data/results",
    "code/logs",
    "specs/001-evaluating-the-impact-of-code-generation/contracts",
]

def create_directories(extra_paths: Optional[List[Path]] = None) -> List[Path]:
    """
    Ensure that all required directories (and any extra_paths) exist.

    Parameters
    ----------
    extra_paths : list of pathlib.Path, optional
        Additional directories that callers may want to guarantee exist.

    Returns
    -------
    list of pathlib.Path
        The absolute paths of all directories that now exist.
    """
    root = _project_root()
    created = []

    # Combine required dirs and extra paths
    all_paths = [root / d for d in _REQUIRED_DIRS]
    if extra_paths:
        all_paths.extend(extra_paths)

    for path in all_paths:
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)

    return created

def main() -> int:
    """
    CLI entry point: create the required layout and exit with status 0
    on success, or 1 on unexpected error.
    """
    try:
        created = create_directories()
        print(f"Successfully created/verified {len(created)} directories.")
        for p in created:
            # Print relative path for cleaner output
            print(f" - {p.relative_to(_project_root())}")
        return 0
    except Exception as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())