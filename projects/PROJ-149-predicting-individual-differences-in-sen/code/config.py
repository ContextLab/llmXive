"""
Configuration for the EEG analysis pipeline.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"

# EEG Parameters
BANDS = {
    'delta': (1, 4),
    'theta': (4, 8),
    'alpha': (8, 13),
    'low_beta': (13, 20),
    'high_beta': (20, 30),
    'gamma': (30, 40)
}
FILTER_PARAMS = {
    'lowcut': 1,
    'highcut': 40,
    'notch': [50, 60]
}
ICA_PARAMS = {
    'n_components': 0.95,
    'random_state': 42
}
WINDOW_SIZE = 4  # seconds
OVERLAP = 0.5
EPSILON = 1e-9
POLY_DEGREE = 2

# Random Seed
RANDOM_SEED = 42

# Path Mapping Configuration
# This dictionary maps logical names to absolute paths
PATH_MAP = {
    'raw': DATA_RAW_DIR,
    'raw_data': DATA_RAW_DIR,
    'interim': DATA_INTERIM_DIR,
    'processed': DATA_PROCESSED_DIR,
    'processed_data': DATA_PROCESSED_DIR,
    'figures': FIGURES_DIR,
    'data_raw': DATA_RAW_DIR,
    'data_interim': DATA_INTERIM_DIR,
    'data_processed': DATA_PROCESSED_DIR,
    'behavioral_metrics': DATA_INTERIM_DIR / "behavioral_metrics.csv",
    'model_results': DATA_PROCESSED_DIR / "model_results.json",
    'features': DATA_PROCESSED_DIR / "features.csv",
}

def get_path(*args):
    """
    Flexible path resolver.
    
    Accepts:
    - get_path("key") -> returns PATH_MAP[key]
    - get_path("key", "subpath") -> returns PATH_MAP[key] / subpath
    - get_path("absolute/path") -> returns Path("absolute/path")
    - get_path(Path_obj) -> returns Path_obj
    
    Handles the various calling conventions found in the project.
    """
    if not args:
        return PROJECT_ROOT
    
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, Path):
            return arg
        if isinstance(arg, str):
            # Check if it's a key in PATH_MAP
            if arg in PATH_MAP:
                return PATH_MAP[arg]
            # Check if it looks like an absolute or relative path string
            if arg.startswith('/') or arg.startswith('./') or arg.startswith('../'):
                return Path(arg)
            # Fallback: treat as a relative path from root or key
            # Try to find it in PATH_MAP keys first (case insensitive maybe?)
            # If not found, assume it's a subpath of PROJECT_ROOT?
            # Or maybe it's a key that wasn't in the map?
            # Let's try to construct it relative to PROJECT_ROOT if it doesn't exist
            p = Path(arg)
            if p.is_absolute():
                return p
            # If it's a relative string, treat as subpath of root?
            # But wait, some calls are get_path("processed", "file.csv")
            # and some are get_path("data/processed/file.csv")
            # If it contains '/', treat as relative path
            if '/' in arg:
                return PROJECT_ROOT / arg
            return PATH_MAP.get(arg, PROJECT_ROOT / arg)
    
    elif len(args) >= 2:
        # get_path("key", "subpath") or get_path(base_dir, subpath)
        first = args[0]
        rest = args[1:]
        
        base = None
        if isinstance(first, Path):
            base = first
        elif isinstance(first, str):
            if first in PATH_MAP:
                base = PATH_MAP[first]
            elif first.startswith('/') or first.startswith('./'):
                base = Path(first)
            else:
                # Maybe it's a relative path string?
                base = PROJECT_ROOT / first
        
        if base is None:
            base = PROJECT_ROOT
        
        # Join the rest
        for part in rest:
            if isinstance(part, Path):
                base = base / part
            elif isinstance(part, str):
                base = base / part
        
        return base
    
    return PROJECT_ROOT

def ensure_dirs(*args):
    """
    Flexible directory creator.
    
    Accepts:
    - ensure_dirs() -> does nothing (or creates root?)
    - ensure_dirs("path") -> creates PROJECT_ROOT / path
    - ensure_dirs(Path_obj) -> creates Path_obj
    - ensure_dirs(["path1", "path2"]) -> creates all
    - ensure_dirs(path_obj, another_obj) -> creates all
    """
    if not args:
        return
    
    paths_to_create = []
    
    for arg in args:
        if isinstance(arg, list):
            paths_to_create.extend(arg)
        elif isinstance(arg, Path):
            paths_to_create.append(arg)
        elif isinstance(arg, str):
            # Check if it's a key in PATH_MAP
            if arg in PATH_MAP:
                paths_to_create.append(PATH_MAP[arg])
            elif '/' in arg or arg.startswith('.'):
                paths_to_create.append(PROJECT_ROOT / arg)
            else:
                # Maybe a simple directory name?
                paths_to_create.append(PROJECT_ROOT / arg)
    
    for p in paths_to_create:
        if isinstance(p, str):
            p = Path(p)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
    
    # Return the last one if needed for chaining, or None
    # Some callers assign the result: output_dir = ensure_dirs(...)
    # We can return the last path created or the first if only one.
    if paths_to_create:
        return paths_to_create[-1]
    return None
