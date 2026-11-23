#!/usr/bin/env python3
"""
Script to create the required project directory structure for
PROJ-395-evaluating-the-impact-of-llm-generated-c.

It creates the following hierarchy relative to the repository root:

    projects/PROJ-395-evaluating-the-impact-of-llm-generated-c/
        data/
        code/
        tests/
        state/

The script is idempotent: running it multiple times will not raise errors.
"""

import sys
from pathlib import Path

def create_structure(base_path: Path) -> None:
    """
    Create the subdirectories `data`, `code`, `tests`, and `state`
    under the given base path.

    Args:
        base_path: Path object pointing to the project root directory.
    """
    subdirs = ["data", "code", "tests", "state"]
    for sub in subdirs:
        (base_path / sub).mkdir(parents=True, exist_ok=True)

def main() -> None:
    """
    Entry point for the script. Constructs the absolute path to the
    project root and creates the required directory tree.
    """
    project_root = Path("projects/PROJ-395-evaluating-the-impact-of-llm-generated-c")
    try:
        create_structure(project_root)
        print(f"Created project structure under: {project_root}", flush=True)
    except Exception as exc:
        print(f"Failed to create project structure: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()