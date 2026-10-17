"""
Project configuration utilities.

This module provides a small set of helper functions used throughout the
codebase to locate standard project directories (raw data, processed data,
logs, figures, etc.) and to ensure they exist. It is deliberately lightweight
and has no external dependencies beyond the standard library and the
`llmxive_toolkit` path utilities that are guaranteed to be present in the
execution environment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

# The llmxive_toolkit provides convenient path factories that automatically
# create parent directories when needed.
from llmxive_toolkit import paths as llm_paths

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# Tolerance used by the outlier detection rule.  The eigen‑solver module
# (`analysis.eigen_solver`) falls back to this constant when no explicit
# tolerance is supplied.
OUTLIER_TOLERANCE: float = 0.05

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_project_paths(root: Optional[Path] = None) -> Dict[str, Path]:
    """
    Return a dictionary with the most common project‑wide directories.

    Parameters
    ----------
    root : pathlib.Path, optional
        The project root. If omitted the root inferred by ``llmxive_toolkit``
        is used.

    Returns
    -------
    dict
        Mapping of logical names to absolute ``Path`` objects:

        - ``root``          – Project root directory.
        - ``raw``           – ``data/raw`` directory.
        - ``processed``     – ``data/processed`` directory.
        - ``logs``          – ``data/logs`` directory.
        - ``figures``       – ``data/figures`` directory.
        - ``results``       – ``data/results`` directory.
        - ``docs``          – ``data/docs`` directory.
    """
    # Resolve the project root; ``llm_paths.root`` is a Path object.
    project_root = root if root is not None else llm_paths.root

    # Build the standard directories using the toolkit helpers.
    # These helpers also ensure the parent directories exist.
    dirs = {
        "root": project_root,
        "raw": llm_paths.data("raw"),
        "processed": llm_paths.data("processed"),
        "logs": llm_paths.data("logs"),
        "figures": llm_paths.figures(),
        "results": llm_paths.results(),
        "docs": llm_paths.docs(),
    }

    return dirs

def ensure_directories(root: Optional[Path] = None) -> None:
    """
    Create all standard project directories if they do not already exist.

    This function is idempotent – calling it repeatedly is safe.
    """
    paths = get_project_paths(root)

    for name, p in paths.items():
        # ``Path.mkdir`` with ``parents=True`` creates any missing ancestors.
        # ``exist_ok=True`` suppresses errors if the directory already exists.
        p.mkdir(parents=True, exist_ok=True)

def get_outlier_tolerance() -> float:
    """
    Return the tolerance used by the outlier validation logic.

    The ``analysis.eigen_solver.validate_eigenvalues`` function falls back
    to this value when the caller does not provide an explicit tolerance.
    """
    return OUTLIER_TOLERANCE
