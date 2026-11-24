"""
Setup Project Layout Script
===========================

This script establishes the required directory structure for the
``PROJ-008-psychology-research`` project, verifies the presence of the
core configuration files (``pyproject.toml`` and ``requirements.txt``),
and records the current Python environment's pinned dependencies to
``docs/install_log.txt``.

It is used by the Quickstart guide and the ``make setup`` target.
The script fails loudly (raises an exception) if any step cannot be
completed, ensuring reproducibility and early detection of problems.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Initialise a logger that writes to the console (and optionally to a file)
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Directory creation
# ----------------------------------------------------------------------
def create_directories(project_root: Path) -> None:
    """
    Create all required directories for the project.

    Parameters
    ----------
    project_root : Path
        The root directory of the repository (``paths.root``).
    """
    required_dirs = [
        "code/data",
        "code/analysis",
        "code/viz",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "docs",
        "contracts",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    for rel_path in required_dirs:
        dir_path = project_root / rel_path
        dir_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {dir_path}")

# ----------------------------------------------------------------------
# Write pip‑freeze output
# ----------------------------------------------------------------------
def write_install_log(project_root: Path) -> None:
    """
    Capture the current environment's pinned packages via ``pip freeze`` and
    write them to ``docs/install_log.txt``.

    Parameters
    ----------
    project_root : Path
        The root directory of the repository.
    """
    log_path = project_root / "docs" / "install_log.txt"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        log.error(f"Failed to run 'pip freeze': {exc}")
        raise

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(result.stdout)

    log.info(f"Wrote pip freeze output to {log_path}")

# ----------------------------------------------------------------------
# Verify core configuration files
# ----------------------------------------------------------------------
def verify_core_files(project_root: Path) -> None:
    """
    Ensure that ``pyproject.toml`` and ``requirements.txt`` exist at the
    repository root.  These files are required for reproducible builds.

    Parameters
    ----------
    project_root : Path
        The root directory of the repository.
    """
    pyproject = project_root / "pyproject.toml"
    requirements = project_root / "requirements.txt"

    if not pyproject.is_file():
        raise FileNotFoundError(f"Missing required file: {pyproject}")

    if not requirements.is_file():
        raise FileNotFoundError(f"Missing required file: {requirements}")

    log.info("Verified presence of pyproject.toml and requirements.txt")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the setup steps.  Any exception propagates and causes a non‑zero
    exit status, which satisfies the “fail loudly” requirement.
    """
    project_root = paths.root
    log.info(f"Project root resolved to: {project_root}")

    create_directories(project_root)
    verify_core_files(project_root)
    write_install_log(project_root)

    log.info("Project layout established successfully.")

if __name__ == "__main__":
    main()
