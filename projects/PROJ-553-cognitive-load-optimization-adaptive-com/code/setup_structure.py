"""
Project Skeleton Setup Script
--------------------------------
Creates the required directory hierarchy and placeholder files for the
Cognitive Load Optimization project. This script is idempotent and can be
run multiple times without side effects.
"""
import sys
from pathlib import Path

# Import the toolkit helper for consistent path handling
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def ensure_dir(path: Path) -> None:
    """
    Ensure a directory exists and contains a ``.gitkeep`` file so that Git
    tracks the empty folder.
    """
    path.mkdir(parents=True, exist_ok=True)
    gitkeep = path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()
    log.info(f"Ensured directory: {path}")

def main() -> None:
    """
    Create all top‑level project directories required by task T001.
    """
    # List of directories to create
    dirs = [
        paths.data("raw"),
        paths.data("processed"),
        paths.data("explanation_tiers"),
        paths.data("simulation_results"),
        paths.code(),
        paths.tests(),
        paths.docs(),
    ]

    for d in dirs:
        ensure_dir(d)

    log.info("Project skeleton initialization complete.")

if __name__ == "__main__":
    # Run the setup when invoked as a script
    main()
