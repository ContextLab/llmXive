"""T001: Establish the project layout for PROJ-008-psychology-research.

Creates the authoritative directory tree under code/ (per the tasks.md
layout note) plus data/, docs/, contracts/, and tests/ subtrees, and
verifies that every expected directory exists afterwards.

Usage:
    python code/setup_project.py
"""
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

REQUIRED_DIRS = [
    "code/data",
    "code/analysis",
    "code/viz",
    "code/lib",
    "code/utils",
    "code/reporting",
    "data/raw",
    "data/processed",
    "data/results",
    "docs",
    "contracts",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]

def setup() -> None:
    """Create all required directories and verify them."""
    for rel in REQUIRED_DIRS:
        d = paths.path(rel)
        d.mkdir(parents=True, exist_ok=True)
        # Keep empty directories in version control.
        keep = d / ".gitkeep"
        if not any(d.iterdir()):
            keep.touch()
        log.info("ready: %s", d)

    missing = [rel for rel in REQUIRED_DIRS if not paths.path(rel).is_dir()]
    if missing:
        raise RuntimeError(f"layout incomplete, missing: {missing}")

    log.info("Project layout verified: %d directories present.", len(REQUIRED_DIRS))

def main() -> int:
    setup()
    print("OK: project layout established under", paths.root)
    return 0

if __name__ == "__main__":
    sys.exit(main())
