"""
check_skeleton.py
-----------------

Utility used by the CI integration test ``tests/ci/test_skeleton_ci.py`` to
verify that the expected repository skeleton exists.  It provides two
public callables:

* ``missing_directories`` – given an iterable of expected directories,
  returns a list of those that are absent.
* ``main`` – the command‑line entry point that exits with status 0 when all
  expected directories are present, otherwise prints the missing ones and
  exits with status 1.
"""

import sys
from pathlib import Path
from typing import Iterable, List


# Expected top‑level directories for the project skeleton.
EXPECTED_DIRS: List[Path] = [
    Path("src"),
    Path("tests"),
    Path("data"),
    Path("results"),
    Path("docs"),
    Path("contracts"),
]


def missing_directories(
    expected: Iterable[Path] = EXPECTED_DIRS, root: Path = Path.cwd()
) -> List[Path]:
    """
    Return a list of directories from ``expected`` that do not exist under
    ``root``.

    Parameters
    ----------
    expected: Iterable[Path]
        The directories that should be present relative to ``root``.
    root: Path
        Base directory to resolve the expected paths against (defaults to the
        current working directory).

    Returns
    -------
    List[Path]
        Paths (relative to ``root``) that are missing.
    """
    missing: List[Path] = []
    for rel_path in expected:
        full_path = root / rel_path
        if not full_path.is_dir():
            missing.append(rel_path)
    return missing


def main() -> None:
    """
    CLI entry point used by CI.  Prints missing directories (if any) and
    exits with a non‑zero status code when the skeleton is incomplete.
    """
    missing = missing_directories()
    if missing:
        print("Missing repository skeleton directories:", file=sys.stderr)
        for d in missing:
            print(f"- {d}", file=sys.stderr)
        sys.exit(1)
    # All directories present – silent success.
    sys.exit(0)


if __name__ == "__main__":
    main()
