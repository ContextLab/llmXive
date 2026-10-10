#!/usr/bin/env python3
"""
create_project_structure.py

Script to create the required project directory tree for
PROJ-505-exploring-the-statistical-relationship-b.

Execution of this script will result in the creation of the following
directories (relative to the repository root):

projects/PROJ-505-exploring-the-statistical-relationship-b/
├─ code/
│  ├─ ingestion/
│  ├─ analysis/
│  └─ utils/
├─ data/
│  ├─ raw/
│  ├─ processed/
│  └─ artifacts/
└─ tests/
   ├─ unit/
   └─ integration/
"""

import sys
from pathlib import Path

def create_dirs(base_path: Path, dirs: list[str]) -> None:
    """Create each directory in ``dirs`` under ``base_path``."""
    for rel_dir in dirs:
        dir_path = base_path / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)

def main() -> int:
    # Determine the repository root (one level up from this script's directory)
    repo_root = Path(__file__).resolve().parents[1]

    target_root = repo_root / "projects" / "PROJ-505-exploring-the-statistical-relationship-b"

    # List of directories to create, relative to target_root
    directories = [
        "code",
        "code/ingestion",
        "code/analysis",
        "code/utils",
        "data",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests",
        "tests/unit",
        "tests/integration",
    ]

    create_dirs(target_root, directories)

    # Optional: create empty __init__.py files to make packages importable
    init_paths = [
        target_root / "code" / "__init__.py",
        target_root / "code" / "ingestion" / "__init__.py",
        target_root / "code" / "analysis" / "__init__.py",
        target_root / "code" / "utils" / "__init__.py",
        target_root / "tests" / "__init__.py",
        target_root / "tests" / "unit" / "__init__.py",
        target_root / "tests" / "integration" / "__init__.py",
    ]
    for init_file in init_paths:
        init_file.touch(exist_ok=True)

    print(f"Created project structure under: {target_root}", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())