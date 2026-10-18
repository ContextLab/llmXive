"""Setup required project directory hierarchy with .gitkeep placeholder files.

This script creates the following directories (if they do not already exist):
  - data/raw/landsat/
  - data/processed/
  - data/ecotourism/
  - data/results/
  - figures/

An empty ``.gitkeep`` file is placed in each directory to ensure the
directory is tracked by git even when it contains no other files.
"""

import logging
from pathlib import Path

# Project‑level utilities
from config import ensure_directories
from logging_config import setup_logging, get_logger

def create_gitkeep(directory: Path) -> None:
    """Create an empty .gitkeep file inside *directory*."""
    gitkeep_path = directory / ".gitkeep"
    # ``touch`` with ``exist_ok`` ensures idempotency.
    gitkeep_path.touch(exist_ok=True)

def main() -> None:
    """Create required directories and populate them with .gitkeep files."""
    # Initialise logging (writes to data/logs/pipeline.log by default)
    setup_logging()
    log: logging.Logger = get_logger(__name__)

    # Ensure any generic project directories are present first.
    # ``ensure_directories`` is defined in ``code/config.py`` and may
    # create top‑level folders such as ``data/`` and ``figures/``.
    try:
        ensure_directories()
    except Exception as exc:
        log.error("ensure_directories failed: %s", exc)
        raise

    # Define the hierarchy relative to the repository root (current working dir).
    root = Path.cwd()
    required_dirs = [
        root / "data" / "raw" / "landsat",
        root / "data" / "processed",
        root / "data" / "ecotourism",
        root / "data" / "results",
        root / "figures",
    ]

    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)
        create_gitkeep(d)
        log.info("Created directory and .gitkeep: %s", d)

if __name__ == "__main__":
    main()