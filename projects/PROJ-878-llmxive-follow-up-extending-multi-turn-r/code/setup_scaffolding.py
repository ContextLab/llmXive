"""
setup_scaffolding.py

Script to create the required project directory structure and ensure that the
essential ``__init__.py`` files are present. This fulfills the scaffolding
verification for task T001.

The script is idempotent – it can be run multiple times without error.
"""

import sys
from pathlib import Path
from llmxive_toolkit import get_logger, paths

# Initialize logger
log = get_logger(__name__)

# Define the required directories relative to the repository root
REQUIRED_DIRS = [
    Path("data/raw"),
    Path("data/processed"),
    Path("data/results"),
    Path("code"),
    Path("code/utils"),
    Path("code/tests"),
    Path("results/paper_figures"),
]

# Define the required __init__.py files
REQUIRED_INIT_FILES = [
    Path("code/__init__.py"),
    Path("code/utils/__init__.py"),
    Path("code/tests/__init__.py"),
]

def ensure_directories() -> None:
    """Create all required directories if they do not already exist."""
    for d in REQUIRED_DIRS:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            log.info(f"Created directory: {d}")
        else:
            log.debug(f"Directory already exists: {d}")

def ensure_init_files() -> None:
    """Create empty __init__.py files where missing."""
    for f in REQUIRED_INIT_FILES:
        if not f.exists():
            f.parent.mkdir(parents=True, exist_ok=True)
            f.touch()
            log.info(f"Created missing __init__: {f}")
        else:
            log.debug(f"__init__ already present: {f}")

def main() -> None:
    """Entry point for the scaffolding setup."""
    log.info("Starting project scaffolding setup...")
    ensure_directories()
    ensure_init_files()
    log.info("Project scaffolding is complete. All required directories and __init__ files are present.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(f"Scaffolding setup failed: {exc}")
        sys.exit(1)
