"""
Init Directories Script
-----------------------

This script creates the full project directory tree required for the
``PROJ-030-predicting-crystal-structures-from-molec`` project and logs the
created directories to ``logs/init.log``.

It is intended to be run after the recovery task (``T001-recovery``) and
before any other task that writes to these directories.
"""

import os
from pathlib import Path
from llmxive_toolkit import paths, get_logger

# Initialize logger – logs will also be written to the file ``logs/init.log``
log = get_logger(__name__, log_file=str(paths.logs("init.log")))

# List of directories to create (relative to the project root)
DIRS_TO_CREATE = [
    # Core data folders
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "data/validation",
    "data/models",
    "data/processing",
    # Logs
    "logs",
    # Source code hierarchy
    "code",
    "code/analysis",
    "code/ingestion",
    "code/modeling",
    "code/utils",
    # Tests
    "tests",
    "tests/unit",
    "tests/integration",
    # Specification and contracts
    "specs",
    "specs/001-predict-crystal-structures",
    "contracts",
    # Additional output folders
    "figures",
    "results",
    "state",
    "state/projects",
]

def create_directories(base_path: Path):
    """Create each directory in ``DIRS_TO_CREATE`` under ``base_path``."""
    created = []
    for rel_dir in DIRS_TO_CREATE:
        dir_path = base_path / rel_dir
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
            log.info(f"Created directory: {dir_path}")
        except Exception as exc:
            log.error(f"Failed to create directory {dir_path}: {exc}")
            raise
    return created

def main():
    """Entry point for the script."""
    project_root = Path(__file__).resolve().parents[2]  # ``code/utils`` -> project root
    log.info(f"Project root resolved to: {project_root}")

    # Create directories
    created_dirs = create_directories(project_root)

    # Write a summary log file (already handled by logger, but also write a plain list)
    init_log_path = paths.logs("init.log")
    try:
        with open(init_log_path, "a") as f:
            f.write("\n=== Directory creation summary ===\n")
            for d in created_dirs:
                f.write(f"{d}\n")
        log.info(f"Directory creation summary written to {init_log_path}")
    except Exception as exc:
        log.error(f"Failed to write summary to {init_log_path}: {exc}")
        raise

    log.info("Project structure initialization completed successfully.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())