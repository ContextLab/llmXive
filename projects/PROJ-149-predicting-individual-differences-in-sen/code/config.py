"""
code/config.py
Central configuration for the project.
Defines paths, filter parameters, ICA settings, and exclusion thresholds.
Provides utility functions used throughout the pipeline.
"""
import os
from pathlib import Path
from typing import Union, List, Any, Tuple
import pathlib

# ----------------------------------------------------------------------
# Project Roots
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / 'data'
CODE_ROOT = PROJECT_ROOT / 'code'

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
EPSILON = 1e-9
OVERLAP = 0.5               # Default overlap ratio for primary analysis
WINDOW_SIZE = 4             # Fixed 4‑second windows for primary analysis
POLY_DEGREE = 2
SEED = 42

# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------
def get_path(*parts: Union[str, Path]) -> Path:
    """
    Flexible path resolver.

    Accepts any number of string or Path arguments and builds a Path
    relative to the project data directory unless an absolute path is given.

    Special handling:
      - If the first part starts with one of the known top‑level folders
        ('raw', 'interim', 'processed', 'figures'), the path is resolved
        under ``data/<folder>/...``.
      - If a single part without a directory is provided (e.g. ``'features_clr'``),
        it is interpreted as a file inside ``data/processed`` with a ``.csv``
        extension (unless the name already contains a file extension).
      - Absolute paths are returned unchanged.
    """
    # Flatten any nested iterable arguments (lists, tuples, sets)
    flat_parts: List[Union[str, Path]] = []
    for p in parts:
        if isinstance(p, (list, tuple, set)):
            flat_parts.extend(p)
        else:
            flat_parts.append(p)

    # If the first part is an absolute path, just join everything and return
    if flat_parts and isinstance(flat_parts[0], (str, Path)):
        first = Path(flat_parts[0])
        if first.is_absolute():
            return Path(*flat_parts)

    # Join parts into a single string for easier inspection
    joined = os.path.join(*[str(p) for p in flat_parts])

    # Absolute path shortcut
    if os.path.isabs(joined):
        return Path(joined)

    # Known top‑level directories
    top_levels = ('raw', 'interim', 'processed', 'figures')
    for tl in top_levels:
        if joined.startswith(f'{tl}/') or joined.startswith(f'{tl}\\'):
            return DATA_ROOT / joined

    # Single filename without directory: assume processed folder
    if '/' not in joined and '\\' not in joined:
        # If no extension, assume .csv for data files
        if '.' not in joined:
            joined = f'{joined}.csv'
        return DATA_ROOT / 'processed' / joined

    # Default: treat as relative to data root
    return DATA_ROOT / joined

def ensure_dirs(*paths: Union[str, Path, List[Union[str, Path]], Tuple[Union[str, Path], ...]]) -> None:
    """
    Create parent directories for the supplied paths.

    Accepts any number of arguments which can be:
      - strings or Path objects
      - lists, tuples or sets containing strings/Path objects
    The function is tolerant of mixed input types and will silently ignore
    ``None`` values.
    """
    def _process(p):
        if p is None:
            return
        # Treat iterable containers (list, tuple, set) as collections of paths
        if isinstance(p, (list, tuple, set)):
            for item in p:
                _process(item)
        else:
            # Convert to Path if necessary
            path_obj = pathlib.Path(p) if not isinstance(p, pathlib.Path) else p
            # If the path points to a file, create its parent directory
            if path_obj.suffix:
                path_obj = path_obj.parent
            path_obj.mkdir(parents=True, exist_ok=True)

    for arg in paths:
        _process(arg)

# ----------------------------------------------------------------------
# Configuration Accessors
# ----------------------------------------------------------------------
def get_filter_params() -> dict:
    """Return band‑pass and notch filter parameters."""
    return {
        'l_freq': 1.0,
        'h_freq': 45.0,
        'notch_freqs': [50.0, 60.0]  # Support 50/60 Hz line noise
    }

def get_ica_params() -> dict:
    """Return ICA configuration."""
    return {
        'n_components': 0.95,   # Retain 95 % variance
        'max_iter': 500
    }

def get_exclusion_params() -> dict:
    """Return EEG channel‑rejection and epoch‑duration parameters."""
    return {
        'variance_threshold_std': 3.0,
        'max_rejected_ratio': 0.30,
        'min_epoch_duration_min': 5.0  # Minimum continuous segment length
    }

def get_band_freqs() -> dict:
    """Canonical frequency bands (Hz)."""
    return {
        'delta': (1.0, 4.0),
        'theta': (4.0, 8.0),
        'alpha': (8.0, 13.0),
        'low_beta': (13.0, 20.0),
        'high_beta': (20.0, 30.0),
        'gamma': (30.0, 45.0)
    }

def get_all_band_names() -> list:
    """List of band names."""
    return list(get_band_freqs().keys())

def get_cv_folds() -> int:
    """Number of cross‑validation folds."""
    return 5

def get_epsilon() -> float:
    """Numerical stability epsilon."""
    return EPSILON

def get_seed() -> int:
    """Random seed for reproducibility."""
    return SEED

# ----------------------------------------------------------------------
# Additional Helper Accessors required by downstream scripts
# ----------------------------------------------------------------------
def get_window_seconds() -> float:
    """
    Return the window size (in seconds) used for PSD computation.
    Primary analysis uses the fixed constant ``WINDOW_SIZE``.
    Robustness runs may override this via CLI arguments.
    """
    return WINDOW_SIZE

def get_overlap_seconds() -> float:
    """
    Return the overlap ratio (as a fraction of the window) for PSD computation.
    Primary analysis defaults to ``OVERLAP``.
    """
    return OVERLAP

def get_min_epoch_duration_minutes() -> float:
    """
    Return the minimum continuous epoch duration (in minutes) required for a participant.
    """
    return get_exclusion_params().get('min_epoch_duration_min', 5.0)

# ----------------------------------------------------------------------
# Configuration Validation
# ----------------------------------------------------------------------
def _validate_numeric(name: str, value: Any, min_val: float = None, max_val: float = None) -> None:
    """Internal helper to validate numeric configuration values."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"Configuration '{name}' must be a numeric type, got {type(value)}.")
    if (min_val is not None) and (value < min_val):
        raise ValueError(f"Configuration '{name}' must be >= {min_val}, got {value}.")
    if (max_val is not None) and (value > max_val):
        raise ValueError(f"Configuration '{name}' must be <= {max_val}, got {value}.")

def validate_config() -> None:
    """
    Validate critical configuration constants.

    Raises:
        ValueError / TypeError: If any configuration is out of the expected range.
    """
    # OVERLAP must be between 0 (exclusive) and 1 (inclusive)
    _validate_numeric('OVERLAP', OVERLAP, min_val=0.0, max_val=1.0)
    if OVERLAP == 0.0:
        raise ValueError("OVERLAP cannot be zero; it would produce no overlap.")

    # WINDOW_SIZE must be a positive number
    _validate_numeric('WINDOW_SIZE', WINDOW_SIZE, min_val=0.0)
    if WINDOW_SIZE <= 0:
        raise ValueError("WINDOW_SIZE must be greater than zero.")

    # POLY_DEGREE must be a positive integer
    if not isinstance(POLY_DEGREE, int) or POLY_DEGREE < 1:
        raise ValueError("POLY_DEGREE must be a positive integer.")

    # SEED must be an integer
    if not isinstance(SEED, int):
        raise TypeError("SEED must be an integer.")

    # EPSILON must be positive
    _validate_numeric('EPSILON', EPSILON, min_val=0.0)

    # Verify band definitions are sensible (non‑overlapping and within 1‑45 Hz)
    bands = get_band_freqs()
    for band_name, (low, high) in bands.items():
        _validate_numeric(f'band {band_name} low', low, min_val=0.0, max_val=high)
        _validate_numeric(f'band {band_name} high', high, min_val=low, max_val=45.0)

    # Ensure that the number of CV folds is at least 2
    if get_cv_folds() < 2:
        raise ValueError("Number of cross‑validation folds must be >= 2.")

# Perform validation at import time so mis‑configurations fail fast
try:
    validate_config()
except Exception as exc:
    # Re‑raise with a clear message; this will abort pipeline start‑up
    raise RuntimeError(f"Configuration validation error: {exc}") from exc

# ----------------------------------------------------------------------
# End of config module
# ----------------------------------------------------------------------