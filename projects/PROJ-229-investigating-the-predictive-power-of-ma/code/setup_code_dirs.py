"""
setup_code_dirs.py
------------------

This module provides a utility to create the standard code sub‑directories for the
project:

- ``code/data``
- ``code/models``
- ``code/utils``
- ``code/validate``

The function ``create_code_directories`` is idempotent – it can be called multiple
times without error – and it also creates an empty ``__init__.py`` file in each
new directory so they are recognised as Python packages.

The script can be executed directly::

    python code/setup_code_dirs.py

which will create the directories (if they do not already exist) and log the
actions performed.
"""

import os
import logging
from pathlib import Path
from typing import List

# The project already provides a logger utility; we import it to keep log
# output consistent with the rest of the code base.
from code.utils.logger import get_pipeline_logger
from config import get_config

LOGGER_NAME = "setup_code_dirs"

def _ensure_package_dir(path: Path) -> None:
    """
    Create a directory and an empty ``__init__.py`` file so that the directory
    is recognised as a Python package.

    Parameters
    ----------
    path: Path
        The directory to create.
    """
    path.mkdir(parents=True, exist_ok=True)
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
    logger.debug(f"Ensured package directory: {path}")

def create_code_directories(base_dir: Path = Path(__file__).parent) -> List[Path]:
    """
    Create the required ``code/*`` sub‑directories.

    Parameters
    ----------
    base_dir: Path, optional
        The root ``code`` directory. By default it is the directory that
        contains this file (i.e. the project's ``code`` folder).

    Returns
    -------
    List[Path]
        A list of the directories that were created or already existed.
    """
    logger = get_pipeline_logger(LOGGER_NAME)

    # Define the relative sub‑directories that must exist.
    subdirs = [
        base_dir / "data",
        base_dir / "models",
        base_dir / "utils",
        base_dir / "validate",
    ]

    created = []
    for subdir in subdirs:
        _ensure_package_dir(subdir)
        created.append(subdir)
        logger.info(f"Created/verified code directory: {subdir}")

    return created

def main() -> None:
    """
    Entry point for ``python code/setup_code_dirs.py``.
    """
    logger = get_pipeline_logger(LOGGER_NAME)
    logger.info("Starting creation of code sub‑directories...")
    created_dirs = create_code_directories()
    logger.info(f"Finished. Created/verified {len(created_dirs)} directories.")

if __name__ == "__main__":
    main()
