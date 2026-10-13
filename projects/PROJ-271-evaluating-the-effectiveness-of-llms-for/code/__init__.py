"""
llmXive Project Code Package

This package initializer ensures that the required project directory layout
exists as soon as the `code` package is imported. The expected layout is:

- data/raw/
- data/processed/
- results/

The helper `ensure_directories` from ``code.create_project_structure`` creates
these top‑level directories if they are missing. Additionally, we use the
``llmxive_toolkit.paths`` helpers to guarantee that the specific sub‑folders
are present.
"""

# Standard library imports
import logging

# Local imports
from .create_project_structure import ensure_directories

# Toolkit imports for convenient path creation
from llmxive_toolkit import paths

# Configure a module‑level logger (optional but useful for debugging)
logger = logging.getLogger(__name__)

def _initialize_package() -> None:
    """
    Perform package‑level initialisation:

    1. Create the top‑level project directories (data/, data/raw/,
       data/processed/, results/).
    2. Explicitly ensure the sub‑folders required by the pipeline exist.
    """
    try:
        # Create the generic top‑level directories
        ensure_directories()
        
        # Ensure the specific sub‑directories used throughout the codebase
        paths.data("raw")          # creates <project>/data/raw/
        paths.data("processed")    # creates <project>/data/processed/
        paths.results()            # creates <project>/results/
        
        logger.debug("Project directory layout verified/created.")
    except Exception as exc:
        # Log the exception but do not suppress it – failing loudly helps
        # the execution stage discover configuration problems early.
        logger.error("Failed to initialise project layout: %s", exc)
        raise

# Run initialisation at import time
_initialize_package()

# Export a clean public interface (optional)
__all__ = []