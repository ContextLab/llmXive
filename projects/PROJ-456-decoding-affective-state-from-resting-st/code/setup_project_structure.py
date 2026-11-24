"""Project structure setup for PROJ-456 (T001).

Creates the directory tree defined in plan.md's Project Structure
section, restricted to PROJECT-OWNED outputs only (code/, data/,
tests/, docs/). The platform owns the top-level ``state/`` directory
and derives artifact hashes at verification time, so this script
never creates or writes into a project-local ``state/`` directory;
if a stale shadow ``state/`` directory exists inside the project
tree (created by an earlier version of this script), it is removed.
"""

import os
import shutil
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Project-owned directories (relative to the project root).
PROJECT_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/templates",
    "data/logs",
    "data/outputs",
    "tests/unit",
    "tests/integration",
    "docs",
]

# Placeholder files required so the package imports cleanly.
PLACEHOLDER_FILES = [
    "code/__init__.py",
    "tests/__init__.py",
    "tests/unit/__init__.py",
    "tests/integration/__init__.py",
]


def create_directory_structure(base_dir: Path) -> None:
    """Create the project-owned directory structure for PROJ-456.

    Required structure (project-owned portions of plan.md):

    projects/PROJ-456-decoding-affective-state-from-resting-st/
        ├── code/
        ├── data/
        │   ├── raw/
        │   ├── processed/
        │   ├── templates/
        │   ├── logs/
        │   └── outputs/
        ├── tests/
        │   ├── unit/
        │   └── integration/
        └── docs/

    Note: ``state/`` is intentionally NOT created — it is owned by
    the platform, which resolves and hashes artifacts there itself.
    """
    base_dir = Path(base_dir)
    for rel in PROJECT_DIRS:
        d = base_dir / rel
        d.mkdir(parents=True, exist_ok=True)
        log.info("Ensured directory: %s", d)

    # Remove any shadow platform-owned directory created by earlier
    # versions of this script. The platform owns `state/`; a copy
    # inside the project is a stale shadow and must not exist.
    shadow_state = base_dir / "state"
    if shadow_state.is_dir():
        shutil.rmtree(shadow_state)
        log.info("Removed shadow platform-owned directory: %s", shadow_state)


def create_placeholder_files(base_dir: Path) -> None:
    """Create essential package placeholder files (``__init__.py``)."""
    base_dir = Path(base_dir)
    for rel in PLACEHOLDER_FILES:
        f = base_dir / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        if not f.exists():
            f.touch()
            log.info("Created placeholder file: %s", f)


def main() -> None:
    """Entry point for project structure setup."""
    base_dir = paths.root
    print(f"Setting up project structure under: {base_dir}")
    create_directory_structure(base_dir)
    create_placeholder_files(base_dir)

    # Verify the expected structure now exists on disk.
    missing = [rel for rel in PROJECT_DIRS if not (base_dir / rel).is_dir()]
    if missing:
        print(f"ERROR: missing directories after setup: {missing}")
        sys.exit(1)
    if (base_dir / "state").exists():
        print("ERROR: shadow state/ directory still present")
        sys.exit(1)

    print("Project structure setup complete (project-owned dirs only).")


if __name__ == "__main__":
    main()