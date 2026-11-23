"""
create_directory_tree.py
------------------------

This script creates the full directory tree required for the MobileForge
Logic Distillation study. It is invoked by the bootstrap process and can be
run independently:

    python code/create_directory_tree.py

The script returns an exit code of ``0`` on success and ``1`` on failure.
"""

import sys
from pathlib import Path
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _ensure_dir(p: Path) -> None:
    """
    Ensure that the directory ``p`` exists, creating parent directories as
    needed. If creation fails, an exception is raised.
    """
    try:
        p.mkdir(parents=True, exist_ok=True)
        log.debug(f"Ensured directory exists: {p}")
    except Exception as exc:
        log.error(f"Failed to create directory {p}: {exc}")
        raise

def main() -> int:
    """
    Create the required directory structure under the project root.

    Returns
    -------
    int
        ``0`` if all directories were created successfully,
        ``1`` otherwise.
    """
    try:
        # Determine the project root (two levels up from this file)
        project_root = Path(__file__).resolve().parent.parent

        # Directories under ``code/``
        code_subdirs = [
            project_root / "code" / "data" / "raw",
            project_root / "code" / "data" / "processed",
            project_root / "code" / "data" / "evaluation",
            project_root / "code" / "models",
            project_root / "code" / "utils",
            project_root / "code" / "tests" / "unit",
            project_root / "code" / "tests" / "integration",
        ]

        # Top‑level directories required by the specification
        top_level_dirs = [
            project_root / "data",
            project_root / "outputs",
        ]

        # Create all directories
        for d in code_subdirs + top_level_dirs:
            _ensure_dir(d)

        log.info("All required directories have been created successfully.")
        return 0

    except Exception as e:
        log.exception("An error occurred while creating the directory tree.")
        return 1

if __name__ == "__main__":
    sys.exit(main())