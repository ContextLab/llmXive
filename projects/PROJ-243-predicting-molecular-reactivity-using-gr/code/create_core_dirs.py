"""
Script to create core project directories and placeholder .gitkeep files.

Directories created:
  - data/raw
  - data/processed
  - data/assets
  - code
  - artifacts
  - tests

Each directory receives a `.gitkeep` file containing a short comment
so that the file is not empty (avoids the “empty file” rejection that
occurs when a .gitkeep is added directly via a static artifact).
The script is idempotent – running it multiple times will not raise
errors and will simply ensure the expected structure exists.
"""

import sys
import logging
from pathlib import Path

# llmxive_toolkit provides convenient path helpers that also ensure
# parent directories exist when called.
from llmxive_toolkit import paths, get_logger

# Use the project's logger (optional but helpful for CI output)
log = get_logger(__name__)

def ensure_dir_and_gitkeep(dir_path: Path) -> None:
    """
    Ensure a directory exists and contains a non‑empty .gitkeep file.

    Parameters
    ----------
    dir_path : Path
        Target directory to create.
    """
    # Create the directory (parents=True is safe even if it already exists)
    dir_path.mkdir(parents=True, exist_ok=True)
    log.debug(f"Ensured directory exists: {dir_path}")

    # Create/overwrite the .gitkeep file with a comment
    gitkeep_path = dir_path / ".gitkeep"
    gitkeep_content = "# Placeholder file to keep the directory tracked by git\n"
    gitkeep_path.write_text(gitkeep_content, encoding="utf-8")
    log.debug(f"Wrote .gitkeep to: {gitkeep_path}")

def main() -> int:
    """Create all required core directories."""
    try:
        # Core data directories
        ensure_dir_and_gitkeep(paths.data("raw"))
        ensure_dir_and_gitkeep(paths.data("processed"))
        ensure_dir_and_gitkeep(paths.data("assets"))

        # Core code directory
        ensure_dir_and_gitkeep(paths.code())

        # Core artifacts directory (used for generated outputs)
        ensure_dir_and_gitkeep(paths.artifacts())

        # Core tests directory
        ensure_dir_and_gitkeep(paths.tests())

        log.info("All core directories and .gitkeep files have been created successfully.")
        return 0
    except Exception as exc:
        log.error(f"Failed to create core directories: {exc}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())