#!/usr/bin/env python
"""
Scaffold creation script for the project.

This script creates the required top‑level directories, places a non‑empty
``.gitkeep`` file in each (including ``metrics/`` and ``logs/``), and
ensures a minimal ``.flake8`` configuration exists at the repository root.
It is idempotent – running it multiple times will not duplicate files.
"""
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

# Initialise a logger that writes to ``logs/scaffold.log``.
# The helper creates the ``logs`` directory if it does not exist.
log_file = paths.logs("scaffold.log")
from code.logging_setup import initialize_logging
initialize_logging(log_file)
log = get_logger(__name__)

def _create_gitkeep(dir_path: Path) -> None:
    """
    Ensure *dir_path* exists and contains a non‑empty ``.gitkeep`` file.
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    gitkeep = dir_path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("# placeholder for git tracking\n", encoding="utf-8")
        log.info(f"Created .gitkeep in {dir_path}")

def _ensure_flake8() -> None:
    """
    Create a minimal ``.flake8`` configuration at the repository root
    if it does not already exist.
    """
    flake8_path = Path.cwd() / ".flake8"
    if not flake8_path.exists():
        flake8_path.write_text("[flake8]\nmax-line-length = 88\n", encoding="utf-8")
        log.info("Created root .flake8 configuration")

def main() -> None:
    """
    Entry point for the scaffold script.
    """
    # Directories that must exist at the project root.
    root = Path.cwd()
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "models",
        "metrics",
        "logs",
        "reports",
        "tests",
        "contracts",
    ]

    for rel in required_dirs:
        _create_gitkeep(root / rel)

    _ensure_flake8()

    log.info("Project scaffold created successfully.")
    print("Project scaffold created successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"Scaffold failed: {e}")
        sys.exit(1)