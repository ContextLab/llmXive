"""
verify_t001b_structure.py
-------------------------
Validation helper used by ``run_t001b.py``.  It checks that the directory
hierarchy defined in ``create_t001b_directories`` exists.  If any required
path is missing an ``AssertionError`` is raised, causing the verification
step to fail loudly (as required by the project’s “fail loudly” policy).
"""

import sys
from pathlib import Path
from typing import List

# The list of directories that must exist – keep it in sync with the
# creation script to avoid false negatives.
_EXPECTED_SUBDIRS: List[Path] = [
    Path("src"),
    Path("tests"),
    Path("data"),
    Path("src/generation"),
    Path("src/filtering"),
    Path("src/training"),
    Path("src/evaluation"),
    Path("src/augmentation"),
    Path("src/utils"),
    Path("tests/unit"),
    Path("tests/integration"),
    Path("data/raw"),
    Path("data/curated"),
    Path("data/eval"),
    Path("data/validation"),
]

def verify_t001b_structure(project_root: Path) -> None:
    """
    Verify that every directory listed in ``_EXPECTED_SUBDIRS`` exists under
    ``project_root``.  Raises ``AssertionError`` with a helpful message if a
    directory is missing.

    Parameters
    ----------
    project_root: Path
        The absolute path to the ``code`` directory of the project.
    """
    missing = [p for p in _EXPECTED_SUBDIRS if not (project_root / p).is_dir()]
    if missing:
        missing_str = ", ".join(str(p) for p in missing)
        raise AssertionError(
            f"The following required directories are missing under "
            f"{project_root!s}: {missing_str}"
        )
    # If we reach this point all required directories are present.
    print("All required T001b directories are present.", file=sys.stderr)

def main() -> None:
    """
    CLI entry point – determines the project root (the parent directory of
    this file) and runs the verification.
    """
    project_root = Path(__file__).resolve().parent
    verify_t001b_structure(project_root)

if __name__ == "__main__":
    main()