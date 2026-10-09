"""
setup_data_dirs.py
------------------

Task **T004**: ensure the required data directory structure exists within
the project repository and that each directory contains a ``.gitkeep``
file so that Git tracks the empty directories.

Public callables matching the project's API surface:

* ``ensure_gitkeep(directory: str) -> None``
* ``main() -> int``

When executed as ``python code/setup_data_dirs.py`` it creates the
following directories under the *project root* (the directory containing
the ``code/`` folder, resolved relative to this file so the script works
regardless of the current working directory):

- ``data/raw``
- ``data/generated``
- ``data/results``

Each directory will contain an empty ``.gitkeep`` file. ``main()``
returns ``0`` on success and ``1`` on failure.
"""

import os
import sys
from typing import List

__all__: List[str] = ["ensure_gitkeep", "main"]

# Project root = parent of the directory containing this file.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ensure_gitkeep(directory: str) -> None:
    """
    Ensure that *directory* exists and contains an empty ``.gitkeep`` file.

    Parameters
    ----------
    directory: str
        Path to the target directory. If relative, it is interpreted
        relative to the current working directory (as in prior versions).
    """
    os.makedirs(directory, exist_ok=True)
    gitkeep_path = os.path.join(directory, ".gitkeep")
    if not os.path.isfile(gitkeep_path):
        with open(gitkeep_path, "a", encoding="utf-8"):
            pass  # The file is now present.


def main() -> int:
    """
    Create the required data sub-directories and their ``.gitkeep`` files.

    Returns
    -------
    int
        Exit status: ``0`` on success, ``1`` on any unexpected error.
    """
    try:
        required_dirs = [
            os.path.join("data", "raw"),
            os.path.join("data", "generated"),
            os.path.join("data", "results"),
        ]

        # Run from the project root so the directories always land in
        # the project tree regardless of the caller's cwd.
        prev_cwd = os.getcwd()
        os.chdir(PROJECT_ROOT)
        try:
            for d in required_dirs:
                ensure_gitkeep(d)
        finally:
            os.chdir(prev_cwd)

        # Verify all three .gitkeep files now exist; fail loudly otherwise.
        for d in required_dirs:
            path = os.path.join(PROJECT_ROOT, d, ".gitkeep")
            if not os.path.isfile(path):
                print(
                    f"[setup_data_dirs] Verification failed: {path} missing",
                    file=sys.stderr,
                )
                return 1

        return 0
    except Exception as exc:
        print(f"[setup_data_dirs] Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
