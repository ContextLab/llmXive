"""
create_directories.py
---------------------

This script implements task **T001**: initialize the project directory structure.

Required directories (relative to the repository root):
  - projects/PROJ-546-predicting-molecular-properties-from-qua/
  - projects/PROJ-546-predicting-molecular-properties-from-qua/code/
  - projects/PROJ-546-predicting-molecular-properties-from-qua/data/raw/
  - projects/PROJ-546-predicting-molecular-properties-from-qua/data/optimized_geometries/
  - projects/PROJ-546-predicting-molecular-properties-from-qua/logs/
  - projects/PROJ-546-predicting-molecular-properties-from-qua/reports/
  - projects/PROJ-546-predicting-molecular-properties-from-qua/specs/001-predicting-molecular-properties-from-qua/contracts/
  - projects/PROJ-546-predicting-molecular-properties-from-qua/tests/unit/
  - projects/PROJ-546-predicting-molecular-properties-from-qua/tests/integration/
  - projects/PROJ-546-predicting-molecular-properties-from-qua/tests/contract/

The script is idempotent: existing directories are left untouched.
Any failure to create a directory raises an exception, causing a non‑zero exit status.

Usage (CLI):
    python -m code.create_directories

The script is also importable; the public function `create_directories()` can be
called from other code (e.g., in test fixtures) to guarantee the required layout
before any pipeline step runs.
"""

import sys
from pathlib import Path
from typing import List

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def create_directories() -> None:
    """
    Create the full directory hierarchy required by the project.

    The hierarchy mirrors the specification in `tasks.md` for task T001.
    If a directory already exists the function does nothing; otherwise it
    creates the directory (including any missing parents).

    Raises:
        OSError: If a directory cannot be created.
    """
    # Base project root – the directory that contains this script's parent folder.
    # This script lives in <repo_root>/projects/PROJ-546-predicting-molecular-properties-from-qua/code/
    # So the project root is two levels up.
    project_root = Path(__file__).resolve().parents[2]

    # Define all required directories relative to the project root.
    required_dirs: List[Path] = [
        project_root / "projects" / "PROJ-546-predicting-molecular-properties-from-qua",
        project_root / "projects" / "PROJ-546-predicting-molecular-properties-from-qua" / "code",
        project_root / "projects" / "PROJ-546-predicting-molecular-properties-from-qua" / "data" / "raw",
        project_root / "projects" / "PROJ-546-predicting-molecular-properties-from-qua" / "data" / "optimized_geometries",
        project_root / "projects" / "PROJ-546-predicting-molecular-properties-from-qua" / "logs",
        project_root / "projects" / "PROJ-546-predicting-molecular-properties-from-qua" / "reports",
        project_root / "projects" / "PROJ-546-predicting-molecular-properties-from-qua" / "specs" / "546-predicting-molecular-properties" / "contracts",
        project_root / "projects" / "PROJ-546-predicting-molecular-properties-from-qua" / "tests" / "unit",
        project_root / "projects" / "PROJ-546-predicting-molecular-properties-from-qua" / "tests" / "integration",
        project_root / "projects" / "PROJ-546-predicting-molecular-properties-from-qua" / "tests" / "contract",
    ]

    for d in required_dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            # Re‑raise with a clearer message; the caller (or CI) will see a non‑zero exit.
            raise OSError(f"Failed to create directory {d}: {exc}") from exc

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI wrapper: create the directories and exit with status 0 on success,
    non‑zero on failure.
    """
    try:
        create_directories()
        print("Project directory structure created successfully.")
    except Exception as e:
        print(f"Error while creating directories: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
