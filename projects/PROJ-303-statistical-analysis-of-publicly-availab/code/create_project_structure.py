"""
create_project_structure.py

This script creates the required project directory hierarchy and places empty
``__init__.py`` files in every package directory under ``src`` and ``tests``.
It is idempotent – running it multiple times will not raise errors or overwrite
existing files.
"""

import os
from pathlib import Path
from typing import List

def _make_dirs(dirs: List[str]) -> None:
    """Create each directory in ``dirs`` (including parents)."""
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def _touch_init_files(dirs: List[str]) -> None:
    """Create an empty ``__init__.py`` in each supplied directory."""
    for d in dirs:
        init_path = Path(d) / "__init__.py"
        # ``touch`` with ``exist_ok`` ensures the file exists without truncating it.
        init_path.touch(exist_ok=True)

def main() -> None:
    """
    Create the full project layout required by task T001.

    Directories created:
        src/{data,models,evaluation,visualization,pipeline,scripts,cli}
        tests/{unit,integration,contract}
        data/{raw,processed}
        outputs/{plots,metrics}
        state

    An empty ``__init__.py`` file is added to every directory under ``src`` and
    ``tests`` (including the top‑level ``src`` and ``tests`` folders themselves).
    """
    # Base directories to create
    base_dirs = [
        "src",
        "src/data",
        "src/models",
        "src/evaluation",
        "src/visualization",
        "src/pipeline",
        "src/scripts",
        "src/cli",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "outputs/plots",
        "outputs/metrics",
        "state",
    ]

    # Create the directories
    _make_dirs(base_dirs)

    # Directories that should be Python packages (need __init__.py)
    package_dirs = [d for d in base_dirs if d.startswith("src") or d.startswith("tests")]
    _touch_init_files(package_dirs)

if __name__ == "__main__":
    # When executed directly, run the creation routine.
    main()