"""
Project structure initialization script.

This script creates the required top‑level directories for the research
project and ensures that ``src`` and ``tests`` are recognised as Python
packages by creating empty ``__init__.py`` files inside them.

It is idempotent – running it multiple times will not raise errors or
overwrite existing files.
"""

import os
from pathlib import Path
import logging
from llmxive_toolkit import get_logger

# Use the shared logger utility; if unavailable, fall back to basicConfig.
try:
    log = get_logger(__name__)  # type: ignore
except Exception:  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

def create_directory(dir_path: Path) -> None:
    """Create a directory and all missing parents."""
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        log.info("Created directory: %s", dir_path)
    else:
        log.debug("Directory already exists: %s", dir_path)

def ensure_init_file(package_path: Path) -> None:
    """Create an empty ``__init__.py`` file so the directory is a package."""
    init_file = package_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        log.info("Created package marker: %s", init_file)
    else:
        log.debug("Package marker already exists: %s", init_file)

def main() -> None:
    """
    Create the required project skeleton:

    - src/
    - tests/
    - data/
    - figures/
    - logs/
    - report/
    - artifacts/

    ``src`` and ``tests`` become importable packages via an ``__init__.py``
    file.
    """
    project_root = Path(__file__).resolve().parent.parent  # repository root
    log.info("Project root resolved to: %s", project_root)

    # Directories to create
    dirs = [
        "src",
        "tests",
        "data",
        "figures",
        "logs",
        "report",
        "artifacts",
    ]

    for d in dirs:
        create_directory(project_root / d)

    # Ensure package markers
    ensure_init_file(project_root / "src")
    ensure_init_file(project_root / "tests")

    log.info("Project structure initialization complete.")

if __name__ == "__main__":
    main()