"""
create_project_structure.py

This script creates the required top‑level project directories for the
llmXive pipeline: `src/`, `tests/`, `data/`, and `results/`. It is
idempotent – running it multiple times will not raise errors if the
directories already exist.

The script is intended to be executed as part of task T001. After execution
the integration test `tests/integration/test_structure.py` will verify the
presence of the directories.
"""

import sys
from pathlib import Path

# The llmxive_toolkit provides a convenient root path helper.
# Import lazily to avoid import errors if the toolkit is not available
# during static analysis.
try:
    from llmxive_toolkit import paths
    project_root = paths.root
except Exception:  # pragma: no cover
    # Fallback: assume the script is run from the repository root.
    project_root = Path.cwd()

# List of directories that must exist at the repository root.
REQUIRED_DIRS = ["src", "tests", "data", "results"]

def create_directories(base: Path) -> None:
    """Create each required directory under ``base`` if it does not exist."""
    for dirname in REQUIRED_DIRS:
        dir_path = base / dirname
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        except Exception as exc:  # pragma: no cover
            print(f"Failed to create {dir_path}: {exc}", file=sys.stderr)
            raise

if __name__ == "__main__":
    create_directories(project_root)