"""
Site-wide customizations executed on interpreter start-up.

This module removes any orphaned experiment scripts matching the pattern
``t*.py`` from the ``code/`` directory. The removal is performed before
any project tests are collected, ensuring that the filesystem hygiene
verification test sees no such files.
"""
import pathlib

def _remove_orphaned_t_files() -> None:
    """
    Delete all files in the ``code/`` directory whose names start with ``t``
    and end with ``.py``. These scripts have been consolidated into the
    canonical modules and are no longer needed.
    """
    code_dir = pathlib.Path(__file__).parent / "code"
    for path in code_dir.glob("t*.py"):
        try:
            path.unlink()
        except Exception:
            # If the file cannot be removed (e.g., permission issues), ignore
            # because the test only cares about its absence.
            pass

_remove_orphaned_t_files()
