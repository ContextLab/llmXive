import json
from pathlib import Path
from typing import Any, Dict, List

# ----------------------------------------------------------------------
# Project-wide constants
# ----------------------------------------------------------------------
# Random seed for reproducibility
SEED: int = 42

# List of target repositories for PR extraction
TARGET_REPOS: List[str] = [
    "microsoft/vscode",
    "pytorch/pytorch",
    "tensorflow/tensorflow",
]

# Hyper‑parameters that control the pipeline behaviour
HYPERPARAMS: Dict[str, Any] = {
    "max_prs": 500,
    "inference_timeout_seconds": 300,
    "similarity_threshold": 0.85,
    "jaccard_threshold": 0.5,
    "line_tolerance": 5,
    "batch_size": 8,
}

# Base directory (project root) – resolved relative to this file
BASE_DIR = Path(__file__).resolve().parents[1]

# Standardised paths used throughout the project
PATHS: Dict[str, Path] = {
    "base": BASE_DIR,
    "data_raw": BASE_DIR / "data" / "raw",
    "data_derived": BASE_DIR / "data" / "derived",
    "data_annotations": BASE_DIR / "data" / "annotations",
    "results": BASE_DIR / "results",
    "specs": BASE_DIR / "specs",
    "logs": BASE_DIR / "logs",
    "tests": BASE_DIR / "tests",
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_config() -> Dict[str, Any]:
    """Load optional user configuration from ``config/config.json``."""
    config_path = BASE_DIR / "config" / "config.json"
    if config_path.is_file():
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_target_repos() -> List[str]:
    """Return the list of repositories to process."""
    # Allow overriding via a user config file
    cfg = get_config()
    return cfg.get("target_repos", TARGET_REPOS)

def get_paths() -> Dict[str, Path]:
    """Return the dictionary of project paths."""
    return PATHS

def ensure_directories() -> None:
    """Create all required directories if they do not exist."""
    for p in PATHS.values():
        p.mkdir(parents=True, exist_ok=True)

def save_config(config: Dict[str, Any], config_path: Path | None = None) -> None:
    """Write a configuration dictionary to ``config.json``."""
    if config_path is None:
        config_path = BASE_DIR / "config" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, sort_keys=True)

def load_config(config_path: Path | None = None) -> Dict[str, Any]:
    """Load a configuration dictionary from ``config.json``."""
    if config_path is None:
        config_path = BASE_DIR / "config" / "config.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)