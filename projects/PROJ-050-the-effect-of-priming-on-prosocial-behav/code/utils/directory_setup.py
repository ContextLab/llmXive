"""
Utility module to create the required data directory structure for the project.

This module defines the list of required directories and provides a function
to create them under the project root. It also creates the legacy ``results``
directory as well as the newer ``data/results`` directory required by the
specification and tests.
"""

import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Project root (can be monkey‑patched in tests)
# ----------------------------------------------------------------------
PROJECT_ROOT: Path = paths.root

# ----------------------------------------------------------------------
# Required directories (as strings relative to PROJECT_ROOT)
# ----------------------------------------------------------------------
# The test suite expects the following entries:
#   - "data/raw"
#   - "data/processed"
#   - "data/validation"
#   - "results"               (legacy top‑level folder)
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/validation",
    "results",
]

def create_directory_structure(logger: None | object = None) -> bool:
    """
    Create the directory hierarchy defined in ``REQUIRED_DIRS`` and also
    ``data/results`` (the new location for result artefacts).

    Parameters
    ----------
    logger : optional
        A ``logging.Logger`` instance. If ``None`` the module‑level
        ``get_logger`` is used.

    Returns
    -------
    bool
        ``True`` if all directories were created (or already existed);
        ``False`` otherwise.
    """
    if logger is None:
        logger = get_logger(__name__)

    success = True

    # Create each required directory
    for rel_path in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / rel_path
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info("Created directory %s", dir_path)
        except Exception as exc:  # pragma: no cover – unexpected OS errors
            logger.error("Failed to create %s: %s", dir_path, exc)
            success = False

    # Ensure the newer ``data/results`` location exists as well
    data_results_path = PROJECT_ROOT / "data" / "results"
    try:
        data_results_path.mkdir(parents=True, exist_ok=True)
        logger.info("Created directory %s", data_results_path)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create %s: %s", data_results_path, exc)
        success = False

    return success

def main() -> None:
    """
    CLI entry point. Exits with a non‑zero status code if any directory
    could not be created.
    """
    logger = get_logger(__name__)
    if not create_directory_structure(logger):
        sys.exit(1)
