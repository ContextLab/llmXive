import os
from pathlib import Path
from typing import Any, Dict

def get_project_root() -> Path:
    """
    Return the absolute path to the project's root directory.
    """
    return Path(__file__).resolve().parents[1]

def ensure_directories() -> None:
    """
    Create the standard data directories used throughout the pipeline.
    """
    root = get_project_root()
    for sub in [
        "data/raw",
        "data/processed",
        "data/final",
        "data/final/plots",
        "logs",
    ]:
        (root / sub).mkdir(parents=True, exist_ok=True)

def get_config_dict() -> Dict[str, Any]:
    """
    Return a dictionary of configuration values.  For the thin pipeline
    we only expose a minimal set.
    """
    return {
        "random_seed": 42,
        "msd_dataset": "matthewfranglen/lastfm-1k",
        "msd_stream_limit": 50000,
    }