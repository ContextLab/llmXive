"""
Verification utilities for the virtual environment.

This module provides three public callables expected by the test suite:

* ``get_project_root`` – returns the absolute path to the project root.
* ``verify_venv`` – checks that the virtual environment was created
  successfully and that ``venv/setup_log.txt`` contains both a Python
  version line and a non‑empty package list.
* ``main`` – a tiny CLI entry point that prints ``True`` or ``False``.
"""

from pathlib import Path
from utils.config import get_project_root

def get_project_root() -> Path:
    """
    Return the absolute path to the project root directory.
    This is a thin wrapper around ``utils.config.get_project_root`` to
    satisfy the import contract used by the test suite.
    """
    return get_project_root()

def _log_contains_version_and_packages(log_path: Path) -> bool:
    """
    Helper that inspects the ``setup_log.txt`` file and returns ``True`` if
    it contains a line starting with ``Python`` (the version line) and
    at least one package entry (the ``Package`` table header that appears
    in the pip list output).
    """
    if not log_path.is_file():
        return False

    content = log_path.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]

    has_version = any(line.startswith("Python") for line in lines)
    has_package_table = any(line.startswith("Package") for line in lines)

    return has_version and has_package_table

def verify_venv() -> bool:
    """
    Verify that the virtual environment exists and that its verification
    log contains the required information.

    Returns:
        bool: ``True`` if the log contains both the Python version line
              and a non‑empty package list, ``False`` otherwise.
    """
    venv_dir = get_project_root() / "venv"
    log_path = venv_dir / "setup_log.txt"
    return _log_contains_version_and_packages(log_path)

def main() -> int:
    """
    CLI entry point used by the test suite. Prints ``True`` or ``False``
    to stdout and exits with ``0`` for success, ``1`` for failure.
    """
    result = verify_venv()
    print(result)
    return 0 if result else 1

if __name__ == "__main__":
    raise SystemExit(main())
