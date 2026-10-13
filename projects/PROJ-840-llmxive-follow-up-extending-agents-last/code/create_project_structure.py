"""
Script to create the required project directory structure for the llmXive ALE Extension
project. This script is idempotent – it will create any missing directories and
leave existing ones untouched.

The required top‑level directories are:
  - code/
  - tests/
  - data/
  - docs/

Within these top‑level folders the following sub‑directories are expected
(as defined in `specs/001-llmxive-follow-up-extending-agents-last/plan.md`):

  code/
    data/
    classification/
    intervention/
    analysis/
    utils/
  tests/
    unit/
    integration/
    contract/
  data/
    raw/
    processed/
  docs/

The script uses the project's `llmxive_toolkit.paths` helper to resolve
paths inside the repository root, ensuring that the directories are created
in the correct location regardless of the current working directory.
"""

import sys
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Define the directory hierarchy relative to the project root
DIR_STRUCTURE = {
    "code": [
        "data",
        "classification",
        "intervention",
        "analysis",
        "utils",
    ],
    "tests": [
        "unit",
        "integration",
        "contract",
    ],
    "data": [
        "raw",
        "processed",
    ],
    "docs": [],
}

def ensure_directories(base: Path, subdirs: list[str]) -> None:
    """
    Ensure that each subdirectory under ``base`` exists.
    ``base`` is created automatically if it does not exist.
    """
    for sub in subdirs:
        dir_path = base / sub
        dir_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Ensured directory: {dir_path}")

def main() -> int:
    """
    Create the full directory tree. Returns an exit code compatible with CI
    expectations (0 = success, non‑zero = failure).
    """
    try:
        for top_dir, subdirs in DIR_STRUCTURE.items():
            top_path = paths.path(top_dir)  # creates the top‑level folder
            log.info(f"Ensured top‑level directory: {top_path}")
            ensure_directories(top_path, subdirs)
        log.info("Project directory structure created successfully.")
        return 0
    except Exception as exc:
        log.error(f"Failed to create directory structure: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())