"""
Utilities to bootstrap the repository layout for the project.

This file is referenced by the quick‑start script and CI to guarantee that
the top‑level directories (code/, data/, docs/, tests/) exist and that each
package under ``code/`` contains an ``__init__.py`` so imports work.
"""

import os
from pathlib import Path


def ensure_directories() -> None:
    """
    Create all required top‑level directories if they do not already exist.
    The function is idempotent – repeated calls are safe.
    """
    for folder in ["code", "data", "docs", "tests"]:
        Path(folder).mkdir(parents=True, exist_ok=True)


def ensure_init_files() -> None:
    """
    Ensure that every package directory under ``code/`` contains an
    ``__init__.py`` file. Existing files are left untouched.
    """
    code_root = Path("code")
    for root, dirs, _ in os.walk(code_root):
        for d in dirs:
            init_path = Path(root) / d / "__init__.py"
            if not init_path.is_file():
                init_path.touch()


def main() -> None:
    """
    Entry point used by the quick‑start and by CI. It creates the
    directory layout and guarantees importability of all ``code/*``
    packages.
    """
    ensure_directories()
    ensure_init_files()


if __name__ == "__main__":
    main()
