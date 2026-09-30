"""
setup_project_structure.py
--------------------------

This module creates the standard project directory hierarchy required for the
repository to pass the T001 verification step. It ensures that the following
directories exist (creating them if necessary) and places a ``.gitkeep`` file
inside each to keep empty directories under version control:

- code/
- data/
- data/raw/
- data/processed/
- data/consent/
- tests/

It also creates a non‑empty ``README.md`` at the repository root if one does
not already exist.

The script can be executed directly:

    python code/setup_project_structure.py

which will perform the setup and log the actions performed.
"""

import logging
from pathlib import Path

from config import (
    get_project_root,
    get_code_dir,
    get_data_dir,
    get_raw_data_dir,
    get_processed_data_dir,
    get_consent_dir,
    get_tests_dir,
)
from logging_config import setup_logging, get_logger

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _ensure_dir(path: Path) -> None:
    """
    Ensure a directory exists and contains a ``.gitkeep`` file.

    Parameters
    ----------
    path: Path
        The directory to create.
    """
    path.mkdir(parents=True, exist_ok=True)
    gitkeep = path / ".gitkeep"
    # Touch the file; ``exist_ok=True`` avoids overwriting if it already exists.
    gitkeep.touch(exist_ok=True)


def create_directories() -> None:
    """
    Create the required project directory hierarchy.

    The function is idempotent – running it multiple times will not raise
    errors and will leave the directory layout unchanged.
    """
    logger = get_logger(__name__)

    # List of directories to create
    dirs = [
        get_project_root(),
        get_code_dir(),
        get_data_dir(),
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir(),
        get_tests_dir(),
    ]

    for d in dirs:
        _ensure_dir(Path(d))
        logger.info("Ensured directory exists: %s", d)

    # Ensure a non‑empty README.md at the repository root
    readme_path = Path(get_project_root()) / "README.md"
    if not readme_path.is_file():
        readme_content = (
            "# Project Title\\n"
            "\\n"
            "This repository contains the implementation of the "
            "`the-impact-of-text-message-tone-on-perce` study.  The "
            "project structure was generated automatically by "
            "`setup_project_structure.py`.\\n"
        )
        readme_path.write_text(readme_content, encoding="utf-8")
        logger.info("Created README.md at %s", readme_path)
    else:
        logger.info("README.md already exists at %s", readme_path)


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for ``python code/setup_project_structure.py``.
    """
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting project structure setup")
    create_directories()
    logger.info("Project structure setup complete")


if __name__ == "__main__":
    main()
