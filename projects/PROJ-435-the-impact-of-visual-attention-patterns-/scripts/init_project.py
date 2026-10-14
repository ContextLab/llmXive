"""
Script to initialize the canonical project directory structure.

This script creates the following empty directories relative to the project root:
  - code/
  - data/raw/
  - data/derived/
  - data/processed/
  - tests/
  - state/
  - output/
  - docs/

It exposes a helper function ``setup_project_structure()`` that can be imported
by other modules or called directly when the script is executed.
The function is idempotent – running it multiple times will not raise errors.
"""

import logging
from pathlib import Path

# Configure a simple logger for this script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

def _project_root() -> Path:
    """
    Resolve the project root directory (the parent of the ``scripts`` folder).

    Returns
    -------
    Path
        Absolute path to the project root.
    """
    return Path(__file__).resolve().parent.parent

def setup_project_structure() -> None:
    """
    Create the canonical directory tree for the project.

    The directories are created with ``parents=True`` and ``exist_ok=True`` so
    that the call is safe to repeat. If any of the directories cannot be
    created (e.g., due to permission errors), an exception will be raised,
    causing the script to exit with a non‑zero status.
    """
    root = _project_root()
    dirs = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "derived",
        root / "data" / "processed",
        root / "tests",
        root / "state",
        root / "output",
        root / "docs",
    ]

    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            log.info("Created directory: %s", d)
        except Exception as exc:
            log.error("Failed to create directory %s: %s", d, exc)
            raise

def main() -> None:
    """
    Entry point for command‑line execution.

    Calls ``setup_project_structure()`` and exits with status 0 on success.
    Any unhandled exception will cause a non‑zero exit code, satisfying the
    verification step that the script must exit cleanly.
    """
    log.info("Initializing project directory structure...")
    setup_project_structure()
    log.info("Project structure initialized successfully.")

if __name__ == "__main__":
    main()