"""
create_directories.py

Utility script to initialize the required project directory structure for
PROJ-546-predicting-molecular-properties-from-qua.

This script is invoked by task T001. It creates the following directories
relative to the repository root:

projects/
  PROJ-546-predicting-molecular-properties-from-qua/
    code/
    data/
      raw/
      optimized_geometries/
    logs/
    reports/
    specs/
      546-predicting-molecular-properties/
        contracts/
    tests/
      unit/
      integration/
      contract/
"""

import sys
from pathlib import Path

def create_directories() -> None:
    """
    Create the full directory hierarchy required by the project.

    The function is idempotent – existing directories are left untouched.
    Any failure to create a directory raises an exception, causing the
    script to exit with a non‑zero status.
    """
    # Repository root (parent of this file's directory)
    repo_root = Path(__file__).resolve().parent.parent

    # Base project directory
    project_dir = repo_root / "projects" / "PROJ-546-predicting-molecular-properties-from-qua"

    # Define all required sub‑paths relative to the project directory
    subdirs = [
        project_dir / "code",
        project_dir / "data" / "raw",
        project_dir / "data" / "optimized_geometries",
        project_dir / "logs",
        project_dir / "reports",
        project_dir / "specs" / "546-predicting-molecular-properties" / "contracts",
        project_dir / "tests" / "unit",
        project_dir / "tests" / "integration",
        project_dir / "tests" / "contract",
    ]

    # Create each directory, including any missing parents
    for d in subdirs:
        d.mkdir(parents=True, exist_ok=True)

    # Also ensure the top‑level `projects` folder exists (in case it was missing)
    (repo_root / "projects").mkdir(parents=True, exist_ok=True)

    # Provide a simple console summary
    print("Project structure created under:", project_dir)
    for d in subdirs:
        print("  -", d.relative_to(repo_root))

def main() -> None:
    """CLI entry point."""
    try:
        create_directories()
    except Exception as exc:
        print(f"Error while creating project structure: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
