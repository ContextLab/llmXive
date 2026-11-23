import os
from pathlib import Path
from typing import Any, Dict

# Research Thresholds
LEVENSHTEIN_THRESHOLD = 4
MATCH_RATE_THRESHOLD = 0.8
RANDOM_SEED = 42

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
    Return a dictionary of configuration values.
    """
    return {
        "random_seed": RANDOM_SEED,
        "levenshtein_threshold": LEVENSHTEIN_THRESHOLD,
        "match_rate_threshold": MATCH_RATE_THRESHOLD,
        "msd_dataset": "matthewfranglen/lastfm-1k",
        "msd_stream_limit": 50000,
    }
