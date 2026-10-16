"""
Configuration module for the research pipeline.

Provides:
- Hyper‑parameters (HYPERPARAMS)
- Path constants (PATHS)
- Random seed (SEED)
- Target repositories (TARGET_REPOS)
- Helper functions to load/save a user configuration file.
- Utility to ensure required directories exist.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# ----------------------------------------------------------------------
# Project‑wide constants
# ----------------------------------------------------------------------
# Random seed used throughout the pipeline (reproducibility)
SEED: int = 42

# Target GitHub repositories for PR extraction (FR‑001)
TARGET_REPOS: List[str] = [
    "microsoft/vscode",
    "pytorch/pytorch",
    "tensorflow/tensorflow",
]

# Hyper‑parameters that can be overridden via a user config file
HYPERPARAMS: Dict[str, Any] = {
    # Maximum number of PRs per repository (default matches the spec)
    "max_prs": 500,
    # Token‑budget for LLM inference (seconds per PR)
    "per_pr_timeout_seconds": 300,
    # Diff truncation token budget (used by the preprocessing step)
    "diff_truncate_tokens": 8000,
    # Random seed – kept in sync with the top‑level SEED constant
    "seed": SEED,
}

# ----------------------------------------------------------------------
# Directory layout
# ----------------------------------------------------------------------
# Resolve the repository root (the directory that contains the top‑level
# ``code`` package).  ``settings.py`` lives in ``code/config`` so we go
# two levels up.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Base data directories
_DATA_DIR = _PROJECT_ROOT / "data"
_RESULTS_DIR = _PROJECT_ROOT / "results"
_FIGURES_DIR = _PROJECT_ROOT / "figures"
_LOGS_DIR = _PROJECT_ROOT / "logs"

# Mapping of logical path names to concrete ``Path`` objects.
# Tests (e.g. ``tests/unit/test_preprocess_and_ground_truth.py``) expect
# keys such as ``data_raw``, ``data_derived`` and ``annotations``.
PATHS: Dict[str, Path] = {
    # Raw GitHub payloads
    "data_raw": _DATA_DIR / "raw",
    # Derived/processed JSON artifacts
    "data_derived": _DATA_DIR / "derived",
    # Human annotation files
    "annotations": _DATA_DIR / "annotations",
    # Convenience aliases used by various scripts
    "raw": _DATA_DIR / "raw",
    "annotations_raw": _DATA_DIR / "annotations" / "raw_comments.json",
    "derived_human_confirmations": _DATA_DIR / "derived" / "human_confirmations.json",
    "derived_human_baseline": _DATA_DIR / "derived" / "human_baseline.json",
    "derived_prs_processed": _DATA_DIR / "derived" / "prs_processed.json",
    # Results and figures directories
    "results": _RESULTS_DIR,
    "figures": _FIGURES_DIR,
    "logs": _LOGS_DIR,
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_paths() -> Dict[str, str]:
    """
    Return a dictionary mapping logical names to absolute path strings.

    The values are returned as strings to keep the API flexible – callers
    can wrap them with ``Path`` if they need a ``Path`` object.
    """
    return {key: str(p) for key, p in PATHS.items()}

def ensure_directories(extra_paths: Optional[List[Path]] = None) -> None:
    """
    Create all directories defined in ``PATHS`` and any additional
    ``extra_paths`` supplied by the caller.

    The function is idempotent – existing directories are left untouched.
    """
    # Core pipeline directories
    for p in PATHS.values():
        p.mkdir(parents=True, exist_ok=True)

    # Any extra directories passed in (e.g. temporary test locations)
    if extra_paths:
        for p in extra_paths:
            p.mkdir(parents=True, exist_ok=True)

def get_target_repos() -> List[str]:
    """
    Return the list of GitHub repositories to process.
    """
    return TARGET_REPOS.copy()

# ----------------------------------------------------------------------
# User configuration handling
# ----------------------------------------------------------------------
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "config.json"

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load a JSON configuration file.

    Parameters
    ----------
    config_path: Path | None
        Path to the configuration file. If ``None`` the default location
        ``<repo_root>/config/config.json`` is used.

    Returns
    -------
    dict
        Parsed configuration (empty dict if the file does not exist).
    """
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(f"Failed to load configuration from {path}: {e}")

def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """
    Write a configuration dictionary to JSON.

    Parameters
    ----------
    config: dict
        Configuration data to write.
    config_path: Path | None
        Destination path. If ``None`` the default location is used.
    """
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except OSError as e:
        raise RuntimeError(f"Failed to write configuration to {path}: {e}")

def get_config() -> Dict[str, Any]:
    """
    Convenience wrapper that loads the default configuration file.
    """
    return load_config()

__all__ = [
    "SEED",
    "TARGET_REPOS",
    "HYPERPARAMS",
    "PATHS",
    "get_paths",
    "ensure_directories",
    "get_target_repos",
    "load_config",
    "save_config",
    "get_config",
]