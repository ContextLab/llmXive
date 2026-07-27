"""Create the repository skeleton required for the project.

This script ensures that the top‑level directories expected by the
pipeline exist:

- src/
- tests/
- data/
- results/
- docs/
- contracts/

It is idempotent – existing directories are left untouched.
The script is used by the unit test ``tests/test_skeleton.py`` and can be
executed directly via ``python code/create_skeleton.py``.
"""

import sys
from pathlib import Path


# List of directories that constitute the repository skeleton.
SKELETON_DIRS = [
    "src",
    "tests",
    "data",
    "results",
    "docs",
    "contracts",
]


def _project_root() -> Path:
    """
    Resolve the project root directory.

    ``create_skeleton.py`` lives in ``code/``; the repository root is the
    parent of that directory.
    """
    return Path(__file__).resolve().parent.parent


def _create_directories(root: Path) -> None:
    """
    Create each directory in ``SKELETON_DIRS`` under ``root``.

    ``parents=True`` ensures that intermediate directories are created if
    they do not already exist, and ``exist_ok=True`` makes the operation
    safe to run multiple times.
    """
    for rel_dir in SKELETON_DIRS:
        dir_path = root / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)


def main(argv: list = None) -> None:
    """
    Entry point for the script.

    Parameters
    ----------
    argv : list, optional
        Command‑line arguments (unused).  The signature matches the style
        used by other scripts in the repository and allows the function to
        be called directly from tests.
    """
    if argv is None:
        argv = sys.argv[1:]  # noqa: F841  (kept for future extensions)

    root = _project_root()
    _create_directories(root)

    # Provide a minimal user‑facing message – useful when the script is run
    # manually.
    print(f"Repository skeleton created under {root}")


if __name__ == "__main__":
    main()
