"""
Constants and utility functions for the Battery Electrolyte Decomposition project.

This module defines the core physical constants, potential values, binning logic,
seed configuration, and helper functions for loading the reaction lookup table
and computing checksums of data directories.

It is deliberately lightweight and has no external side‑effects on import,
making it safe to import from any part of the pipeline.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

# ----------------------------------------------------------------------
# Physical constants
# ----------------------------------------------------------------------
# Faraday constant (Coulombs per mole of electrons)
FARADAY_C = 96485.33212  # C·mol⁻¹

# List of electrochemical potentials (volts) for which we compute targets
PHI_VALUES: List[float] = [0.0, 2.0, 4.0]

# ----------------------------------------------------------------------
# Potential binning
# ----------------------------------------------------------------------
# The specification defines two bins:
#   * Low  : 0 V – 2 V   (covers the 0 V and 2 V data points)
#   * High : 3 V – 5 V   (mapped to the available 4 V data point)
#
# We expose a simple helper that returns the bin label for a given potential.
def get_potential_bin(potential_v: float) -> str:
    """
    Return the bin label ('low' or 'high') for a given potential.

    Parameters
    ----------
    potential_v: float
        The electrochemical potential in volts.

    Returns
    -------
    str
        'low' if 0 ≤ potential ≤ 2, otherwise 'high'.
    """
    if 0.0 <= potential_v <= 2.0:
        return "low"
    # Anything else (including the 4 V point) is treated as high.
    return "high"

# ----------------------------------------------------------------------
# Seed configuration
# ----------------------------------------------------------------------
# A deterministic seed is used throughout the project to make results
# reproducible.  The value can be overridden at runtime via the central
# configuration system (code/config.py), but we provide a sensible default.
DEFAULT_SEED = 42

def get_default_seed() -> int:
    """Return the default random seed for the project."""
    return DEFAULT_SEED

# ----------------------------------------------------------------------
# Reaction lookup table
# ----------------------------------------------------------------------
# The hard‑coded reaction table lives in ``code/utils/reactions.yaml``.
# It follows the schema described in the task description.

_REACTIONS_CACHE: Optional[Dict[str, Any]] = None

def _reactions_yaml_path() -> Path:
    """Convenient helper to locate the reactions.yaml file."""
    # ``__file__`` points to ``code/utils/constants.py``; the yaml file lives
    # in the same directory.
    return Path(__file__).with_name("reactions.yaml")

def load_reactions() -> Dict[str, Any]:
    """
    Load and cache the reaction lookup table.

    Returns
    -------
    dict
        The parsed YAML content.  The top‑level key is ``entries`` which is a
        list of reaction dictionaries.
    """
    global _REACTIONS_CACHE
    if _REACTIONS_CACHE is None:
        yaml_path = _reactions_yaml_path()
        if not yaml_path.exists():
            raise FileNotFoundError(f"Reactions file not found at {yaml_path}")
        with open(yaml_path, "r") as f:
            _REACTIONS_CACHE = yaml.safe_load(f) or {}
    return _REACTIONS_CACHE

# ----------------------------------------------------------------------
# Checksum utilities for data integrity
# ----------------------------------------------------------------------
# The generic checksum helpers live in ``code/data/checksum.py``.  We expose
# thin wrappers here so callers do not need to know the exact import path.

from data.checksum import (
    compute_sha256,
    save_checksums,
    load_checksums,
    validate_file,
    validate_all_checksums,
    register_file,
)

def compute_directory_checksums(
    directory: Path, output_path: Optional[Path] = None
) -> Dict[str, str]:
    """
    Compute SHA‑256 checksums for every regular file in *directory*.

    Parameters
    ----------
    directory: pathlib.Path
        Directory whose files should be checksummed (recursively).
    output_path: pathlib.Path, optional
        If provided, the resulting mapping is written as JSON to this path.

    Returns
    -------
    dict
        Mapping ``{relative_path: checksum}``.
    """
    if not isinstance(directory, Path):
        directory = Path(directory)
    checksums: Dict[str, str] = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(directory))
            checksums[rel_path] = compute_sha256(str(file_path))
    if output_path is not None:
        save_checksums(checksums, str(output_path))
    return checksums

# ----------------------------------------------------------------------
# Public API surface (what other modules may import)
# ----------------------------------------------------------------------
__all__ = [
    "FARADAY_C",
    "PHI_VALUES",
    "get_potential_bin",
    "DEFAULT_SEED",
    "get_default_seed",
    "load_reactions",
    "compute_sha256",
    "save_checksums",
    "load_checksums",
    "validate_file",
    "validate_all_checksums",
    "register_file",
    "compute_directory_checksums",
]
