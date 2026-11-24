"""
setup_structure.py

Script to initialise the required project directory structure for the
Predicting Phase Transitions in Amorphous Solids project.

This script creates the following folders (if they do not already exist):
  - data/raw/
  - data/processed/
  - data/logs/
  - code/
  - code/data/
  - code/models/
  - code/utils/
  - artifacts/models/
  - artifacts/figures/
  - artifacts/reports/
  - tests/
  - docs/

It uses the `llmxive_toolkit.paths` helper to locate the project root.
Running the script is idempotent – existing directories are left untouched.
"""
import sys
from pathlib import Path

# llmxive_toolkit provides a convenient Path helper that points to the project root
from llmxive_toolkit import paths

def _create_directories(root: Path) -> None:
    """
    Create all required directories under the given root path.

    Parameters
    ----------
    root : Path
        The absolute path to the project root directory.
    """
    required_dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "logs",
        root / "code",
        root / "code" / "data",
        root / "code" / "models",
        root / "code" / "utils",
        root / "artifacts" / "models",
        root / "artifacts" / "figures",
        root / "artifacts" / "reports",
        root / "tests",
        root / "docs",
    ]

    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")

def main() -> int:
    """
    Entry point for the script.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    try:
        project_root = Path(paths.root)  # paths.root is a pathlib.Path in the toolkit
        _create_directories(project_root)
        return 0
    except Exception as exc:  # pragma: no cover – any exception should be visible in CI logs
        print(f"Error while creating project structure: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
