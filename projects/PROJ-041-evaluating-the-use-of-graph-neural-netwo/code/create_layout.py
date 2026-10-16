"""
Project layout creation utilities (Task T001).

This module provides three public helpers:
  - ensure_directories(): create the top‑level project folders.
  - ensure_init_files(): add an empty ``__init__.py`` to every package
    directory under ``code/`` so they are importable.
  - main(): entry point that runs both steps.

Running this script as a module will materialise the required directory
tree and package initialisation files.
"""

import os
from pathlib import Path

# Top‑level directories required by the specification
TOP_LEVEL_DIRS = [
    "code",
    "data",
    "docs",
    "tests",
]

# Sub‑packages under ``code`` that should be importable
CODE_SUBPACKAGES = [
    "code",
    "code/utils",
    "code/data",
    "code/models",
    "code/analysis",
]


def ensure_directories() -> None:
    """
    Create all required top‑level directories if they do not already exist.
    The function is idempotent – repeated calls are safe.
    """
    for d in TOP_LEVEL_DIRS:
        Path(d).mkdir(parents=True, exist_ok=True)


def ensure_init_files() -> None:
    """
    Ensure that every package directory under ``code/`` contains an
    ``__init__.py`` file. Existing files are left untouched.
    """
    for pkg_path in CODE_SUBPACKAGES:
        pkg_dir = Path(pkg_path)
        pkg_dir.mkdir(parents=True, exist_ok=True)
        init_file = pkg_dir / "__init__.py"
        if not init_file.is_file():
            init_file.touch()


def main() -> None:
    """
    Entry point used by the quick‑start and by CI. It creates the
    directory layout and guarantees importability of all ``code/*``
    packages.
    """
    ensure_directories()
    ensure_init_files()
    # Optional: create a minimal config.yaml if it does not exist
    config_path = Path("code") / "config.yaml"
    if not config_path.is_file():
        config_path.write_text("active_dataset: null\\n", encoding="utf-8")


if __name__ == "__main__":
    main()