"""
Script to create the required output directories for the project:
- projects/PROJ-065-assessing-the-generalizability-of-statis/outputs/
- projects/PROJ-065-assessing-the-generalizability-of-statis/outputs/figures/
- projects/PROJ-065-assessing-the-generalizability-of-statis/outputs/reports/

This script is idempotent and can be safely re‑run. It logs the creation
of each directory using the project's logger.
"""

import logging
from pathlib import Path

from llmxive_toolkit import get_logger, paths


# Obtain a logger; this will also configure a default console handler.
log = get_logger(__name__)


def ensure_directory(dir_path: Path) -> None:
    """
    Ensure that ``dir_path`` exists. If it does not, create it (including
    any missing parents). Log the action.
    """
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {dir_path}")
    else:
        log.debug(f"Directory already exists: {dir_path}")


def main() -> None:
    """
    Entry point: create the top‑level ``outputs`` directory and its
    sub‑folders ``figures`` and ``reports``.

    The ``paths`` helper creates the parent ``outputs`` folder when we
    request a path inside it, but we explicitly create the sub‑folders
    here to satisfy the task requirement.
    """
    # Root of the project (where the repository lives)
    project_root = Path(paths.root)

    # Define the required directories relative to the project root.
    outputs_dir = project_root / "outputs"
    figures_dir = outputs_dir / "figures"
    reports_dir = outputs_dir / "reports"

    # Ensure each directory exists.
    for d in (outputs_dir, figures_dir, reports_dir):
        ensure_directory(d)

    log.info("All required output directories are ready.")


if __name__ == "__main__":
    main()