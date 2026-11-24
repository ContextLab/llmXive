"""
setup_project_structure.py

Creates the standard project directory layout required for the pipeline:
- src/
- tests/
- data/raw/
- data/processed/
- results/
- docs/
The script is idempotent and can be run repeatedly without error.
"""

import sys
from pathlib import Path
from llmxive_toolkit import get_logger, paths

# Obtain a logger; if the platform configures a log file it will be used.
log = get_logger(__name__)

def _create_dir(dir_path: Path) -> None:
    """
    Ensure a directory exists.

    Parameters
    ----------
    dir_path : Path
        The directory to create (parents are created as needed).
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {dir_path}")
    except Exception as exc:
        log.error(f"Failed to create directory {dir_path}: {exc}")
        raise

def main() -> None:
    """
    Entry point for the project‑structure creation script.

    It creates the following directories relative to the project root:

    - src/
    - tests/
    - data/raw/
    - data/processed/
    - results/
    - docs/
    """
    # Resolve the root of the repository using the toolkit helper.
    root = paths.root

    # Define the directory tree.
    directories = [
        root / "src",
        root / "tests",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "results",
        root / "docs",
    ]

    for d in directories:
        _create_dir(d)

    log.info("Project directory layout created successfully.")

if __name__ == "__main__":
    # When executed as a script we run the main function.
    # Any exception will cause a non‑zero exit code,
    # which satisfies the verification requirement that the script must not fail silently.
    try:
        main()
    except Exception as e:
        log.exception("Unhandled exception during project structure creation")
        sys.exit(1)