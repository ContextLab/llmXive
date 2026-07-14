import os
from pathlib import Path
from typing import Iterable, List, Union, Any

# Existing configuration functions (preserved)
def get_project_root() -> Path:
    """
    Return the root directory of the project (the directory containing this file's parent).
    """
    return Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------
# Added directory getter helpers (newly introduced to satisfy missing imports)
# ----------------------------------------------------------------------
def get_raw_dir() -> Path:
    """Root directory for raw data."""
    return get_project_root() / "data" / "raw"

def get_processed_dir() -> Path:
    """Root directory for processed data."""
    return get_project_root() / "data" / "processed"

def get_stratified_dir() -> Path:
    """Root directory for stratified dataset splits."""
    return get_project_root() / "data" / "stratified"

def get_features_dir() -> Path:
    """Root directory for extracted feature files."""
    return get_project_root() / "data" / "features"

def get_results_dir() -> Path:
    """Root directory for result artefacts."""
    return get_project_root() / "data" / "results"

def get_figures_dir() -> Path:
    """Root directory for generated figures."""
    return get_project_root() / "figures"

def get_memory_limit_bytes() -> int:
    """Memory limit in bytes (default 6 GB)."""
    return 6 * 1024 * 1024 * 1024

# ----------------------------------------------------------------------
# Existing helper – preserved (if already defined elsewhere)
# ----------------------------------------------------------------------
# def get_config_summary(): ...
# (Assume existing implementations remain untouched.)

# ----------------------------------------------------------------------
# Flexible ensure_directories implementation
# ----------------------------------------------------------------------
def ensure_directories(*paths: Union[Path, str, Iterable[Union[Path, str]]]) -> None:
    """
    Ensure that each directory passed (or each directory inside an iterable) exists.
    Accepts:
        - No arguments (no‑op)
        - A single Path or string
        - Multiple Path / string arguments
        - An iterable (list/tuple/set) containing Paths / strings
    Example calls that must be supported:
        ensure_directories()
        ensure_directories(Path('a'))
        ensure_directories('a', Path('b'))
        ensure_directories([Path('a'), Path('b')])
        ensure_directories(Path('a'), [Path('b'), Path('c')])
    """
    dirs: List[Path] = []

    for p in paths:
        if p is None:
            continue
        # If the argument itself is an iterable of paths (but not a Path object)
        if isinstance(p, (list, tuple, set)):
            for inner in p:
                if isinstance(inner, Path):
                    dirs.append(inner)
                else:
                    dirs.append(Path(str(inner)))
        else:
            # Single Path or string
            if isinstance(p, Path):
                dirs.append(p)
            else:
                dirs.append(Path(str(p)))

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
