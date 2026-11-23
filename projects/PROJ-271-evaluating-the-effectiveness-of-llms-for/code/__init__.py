"""
llmXive Project Code Package.

This package initializer ensures that the required project directory
layout exists as soon as the ``code`` package is imported. The expected
layout is:

- data/raw/
- data/processed/
- results/
- tests/unit/
- tests/contract/

Creation is idempotent: importing the package repeatedly is safe.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Project root is the parent of the directory containing this file.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories required by the project layout (T001a / T005).
_REQUIRED_DIRS = [
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "results",
    PROJECT_ROOT / "tests" / "unit",
    PROJECT_ROOT / "tests" / "contract",
]


def _initialize_package() -> None:
    """Create the required project directories if they are missing.

    Fails loudly (re-raises) if the filesystem cannot be written to,
    so configuration problems surface early.
    """
    try:
        for directory in _REQUIRED_DIRS:
            directory.mkdir(parents=True, exist_ok=True)
        logger.debug("Project directory layout verified/created.")
    except Exception as exc:
        logger.error("Failed to initialise project layout: %s", exc)
        raise


# Run initialisation at import time (idempotent).
_initialize_package()

__all__ = ["PROJECT_ROOT"]
