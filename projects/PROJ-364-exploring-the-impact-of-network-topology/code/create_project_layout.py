"""
Script to create the core project layout directories and add placeholder .gitkeep files.
This fulfills task T001: ensuring the standard folder structure exists with .gitkeep
files so that empty directories are tracked by version control.
"""

import os
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Initialize logger (optional; logs to default pipeline logger if configured)
log = get_logger(__name__)

def ensure_dir_and_gitkeep(dir_path: Path) -> None:
    """
    Ensure a directory exists and contains a .gitkeep placeholder file.

    Args:
        dir_path (Path): The directory to create/check.
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    gitkeep_file = dir_path / ".gitkeep"
    if not gitkeep_file.exists():
        gitkeep_file.touch()
        log.info(f"Created .gitkeep in {dir_path}")
    else:
        log.debug(f".gitkeep already exists in {dir_path}")

def main() -> None:
    """
    Create all required top‑level project directories and place .gitkeep files
    inside each of them, **excluding platform‑owned `state/`** which must not be
    written by project code.
    """
    # Define the set of directories required by the project layout
    required_dirs = [
        paths.code(),                     # code/
        paths.data("raw"),                # data/raw/
        paths.data("processed"),          # data/processed/
        paths.results(),                  # results/
        # Exclude paths.path("state") – platform‑owned
        paths.path("contracts"),          # contracts/
        paths.path("logs"),               # logs/
        paths.docs(),                     # docs/
    ]

    for d in required_dirs:
        ensure_dir_and_gitkeep(d)

    # Also ensure a .gitkeep at the top‑level data and results directories
    # (in case they are referenced directly without subfolders)
    for top_dir in [paths.data(), paths.results()]:
        ensure_dir_and_gitkeep(top_dir)

    log.info("Project layout creation complete (state/ excluded).")

if __name__ == "__main__":
    main()
