"""
Script to create the required project directory structure for the
energy‑inequity pipeline.

The directories are created relative to the repository root using the
`paths` helper from ``llmxive_toolkit`` to ensure they are placed inside
the project and that parent folders are created automatically.

This script is idempotent – running it multiple times will not raise an
error if the directories already exist.
"""

from pathlib import Path
from llmxive_toolkit import paths, get_logger

# Configure a logger for this script
log = get_logger(__name__)

def create_directories() -> None:
    """
    Create all directories required by the project.

    The list mirrors the specification in ``tasks.md`` for task T001.
    """
    # Directories under the repository root
    dirs = [
        Path("src/data"),
        Path("src/analysis"),
        Path("src/utils"),
        Path("src/models"),
        Path("tests/unit"),
        Path("tests/integration"),
        Path("data/raw"),
        Path("data/processed"),
        Path("data/outputs"),
        Path("specs"),
    ]

    for d in dirs:
        # Use the ``paths`` helper to get a Path inside the project and
        # ensure the parent directory exists.
        project_path = paths.path(d)  # creates parent directories
        project_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {project_path}")

if __name__ == "__main__":
    create_directories()
