"""
Linting and formatting configuration helper.

This module provides utilities to ensure that Ruff (linting) and Black
(code formatting) configuration files exist at the repository root and
that the required packages are listed in ``requirements.txt``.

The public API matches the names declared in the project’s API surface:

- ``ensure_config_dir`` – prepares the directory where configuration files
  will be written (the repository root in this case).
- ``create_ruff_config`` – writes a minimal ``.ruff.toml`` file.
- ``create_black_config`` – writes a ``pyproject.toml`` containing Black
  configuration.
- ``update_requirements`` – adds ``ruff`` and ``black`` to
  ``requirements.txt`` if they are not already present.
- ``main`` – orchestrates the above steps.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple


def _repo_root() -> Path:
    """
    Return the absolute path to the repository root (the directory that
    contains this script's ``code`` folder).  This function works when the
    script is executed from any working directory.
    """
    # ``__file__`` points to ``code/setup_linting_formatting.py``.
    # The repository root is two levels up.
    return Path(__file__).resolve().parents[1]


def ensure_config_dir() -> Path:
    """
    Ensure that the repository root directory exists (it always does) and
    return its ``Path`` object.  This function exists for API compatibility
    and future extensibility.
    """
    root = _repo_root()
    if not root.is_dir():
        raise FileNotFoundError(f"Repository root not found: {root}")
    return root


def create_ruff_config(root: Path = None) -> Path:
    """
    Create a ``.ruff.toml`` configuration file at ``root`` (defaults to
    the repository root).  If the file already exists, it is overwritten
    with the canonical configuration defined in this repository.

    Returns:
        Path to the created ``.ruff.toml`` file.
    """
    if root is None:
        root = ensure_config_dir()
    ruff_path = root / ".ruff.toml"
    ruff_content = """\
# Ruff configuration
# See https://beta.ruff.rs/docs/configuration/ for details
[tool.ruff]
line-length = 88
select = ["E", "F", "W", "C90"]
ignore = []
target-version = "py311"
"""
    ruff_path.write_text(ruff_content, encoding="utf-8")
    return ruff_path


def create_black_config(root: Path = None) -> Path:
    """
    Create a ``pyproject.toml`` file containing Black configuration at
    ``root`` (defaults to the repository root).  Existing files are
    overwritten.

    Returns:
        Path to the created ``pyproject.toml`` file.
    """
    if root is None:
        root = ensure_config_dir()
    pyproject_path = root / "pyproject.toml"
    black_content = """\
# Pyproject configuration for Black formatting
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
    pyproject_path.write_text(black_content, encoding="utf-8")
    return pyproject_path


def update_requirements(root: Path = None) -> Path:
    """
    Ensure that ``ruff`` and ``black`` are listed in ``requirements.txt``.
    If the file does not exist, it is created.  Duplicate entries are
    avoided.

    Returns:
        Path to the (potentially updated) ``requirements.txt`` file.
    """
    if root is None:
        root = ensure_config_dir()
    req_path = root / "requirements.txt"
    needed = {"ruff", "black"}

    if req_path.is_file():
        existing = {line.strip() for line in req_path.read_text().splitlines() if line.strip()}
    else:
        existing = set()

    missing = needed - existing
    if missing:
        # Append missing requirements, each on its own line.
        with req_path.open("a", encoding="utf-8") as f:
            for pkg in sorted(missing):
                f.write(f"{pkg}\\n")
    return req_path


def main(argv: Tuple[str, ...] = ()) -> int:
    """
    Entry‑point for the script.  It creates the configuration files and
    updates ``requirements.txt``.  The function returns an exit code
    compatible with ``sys.exit``.

    Parameters
    ----------
    argv : Tuple[str, ...]
        Command‑line arguments (ignored; present for testability).

    Returns
    -------
    int
        ``0`` on success, non‑zero on unexpected failure.
    """
    try:
        root = ensure_config_dir()
        create_ruff_config(root)
        create_black_config(root)
        update_requirements(root)
    except Exception as exc:
        print(f"Error configuring linting/formatting: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
