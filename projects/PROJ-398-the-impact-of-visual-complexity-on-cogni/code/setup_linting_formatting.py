"""
setup_linting_formatting.py
---------------------------
This module provides a small CLI utility that creates the linting and formatting
configuration files required by the project and (optionally) adds the corresponding
packages to ``requirements.txt``.

The public API matches the signature declared in the project description:

* ``ensure_config_dir`` – ensures a directory exists (used for future extensions).
* ``create_ruff_config`` – writes a minimal ``.ruff.toml`` to the repository root.
* ``create_black_config`` – writes a ``pyproject.toml`` containing Black settings.
* ``update_requirements`` – appends ``ruff`` and ``black`` to ``requirements.txt`` if
  they are not already present.
* ``main`` – orchestrates the above steps.

The script is deliberately side‑effectful: it writes files *outside* the ``code/``
directory (to the repository root) because the test suite expects the configuration
files to live there.  All paths are computed relative to the location of this file,
so the script works regardless of the current working directory.

Running the script:

.. code-block:: console

    $ python code/setup_linting_formatting.py

will create (or overwrite) the two configuration files and update
``requirements.txt``.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _project_root() -> Path:
    """
    Return the absolute path to the repository root (the parent of the ``code/``
    directory that contains this file).
    """
    return Path(__file__).resolve().parent.parent

def ensure_config_dir() -> Path:
    """
    Ensure that a ``.config`` directory exists at the repository root.
    This directory is not strictly required for the current configuration files
    but provides a convenient place for future extensions (e.g., pre‑commit hooks).
    The function returns the path to the directory.
    """
    config_dir = _project_root() / ".config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

# ---------------------------------------------------------------------------
# Configuration file creators
# ---------------------------------------------------------------------------

def create_ruff_config() -> Path:
    """
    Create a minimal ``.ruff.toml`` file at the repository root.
    
    The configuration enables the default rule set, selects the ``flake8`` and
    ``pycodestyle`` plugins, and formats the output as ``concise``.
    """
    ruff_path = _project_root() / ".ruff.toml"
    ruff_content = """\
[tool.ruff]
line-length = 88
select = ["E", "F", "W", "C90"]
ignore = []
target-version = "py311"
"""
    ruff_path.write_text(ruff_content, encoding="utf-8")
    return ruff_path

def create_black_config() -> Path:
    """
    Create a ``pyproject.toml`` file containing Black configuration.
    
    If a ``pyproject.toml`` already exists, the function merges the Black section
    into the existing file without overwriting unrelated content.
    """
    pyproject_path = _project_root() / "pyproject.toml"
    black_section = """\
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.
    |\\.git
    |\\.hg
    |\\.mypy_cache
    |\\.tox
    |\\.venv
    |_build
    |buck-out
    |build
    |dist
)/
'''
"""
    if pyproject_path.exists():
        # Append the Black section if not already present.
        existing = pyproject_path.read_text(encoding="utf-8")
        if "[tool.black]" not in existing:
            with pyproject_path.open("a", encoding="utf-8") as f:
                f.write("\n" + black_section)
    else:
        # Write a fresh pyproject.toml containing only the Black config.
        pyproject_path.write_text(black_section, encoding="utf-8")
    return pyproject_path

# ---------------------------------------------------------------------------
# Requirements updater
# ---------------------------------------------------------------------------

def update_requirements() -> Path:
    """
    Ensure that ``ruff`` and ``black`` are listed in ``requirements.txt`` at the
    repository root.  The function adds the packages only if they are missing.
    """
    req_path = _project_root() / "requirements.txt"
    # If the file does not exist yet, create a minimal one.
    if not req_path.exists():
        req_path.write_text("", encoding="utf-8")

    existing = {line.strip() for line in req_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    additions = []
    for pkg in ("ruff", "black"):
        if pkg not in existing:
            additions.append(pkg)

    if additions:
        with req_path.open("a", encoding="utf-8") as f:
            for pkg in additions:
                f.write(f"{pkg}\\n")
    return req_path

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: Tuple[str, ...] = ()) -> int:
    """
    Execute the configuration steps.
    
    Parameters
    ----------
    argv: Tuple[str, ...]
        Command‑line arguments (currently ignored; present for future extensibility).
    
    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    try:
        # Step 1: ensure optional config directory exists
        ensure_config_dir()
        # Step 2: create the linting and formatting configuration files
        create_ruff_config()
        create_black_config()
        # Step 3: record the tools in requirements.txt
        update_requirements()
    except Exception as exc:
        sys.stderr.write(f"Error while setting up linting/formatting: {exc}\\n")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))