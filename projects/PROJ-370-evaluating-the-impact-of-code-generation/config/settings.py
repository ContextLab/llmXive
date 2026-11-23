"""
Configuration module for the llmXive evaluation pipeline.

This module provides:
  - Global constants such as TARGET_REPOS and random seed.
  - Hyper‑parameter dictionary (HYPERPARAMS) used across the pipeline.
  - Path constants (PATHS) exposing both directory and common file locations as pathlib.Path objects.
  - Helper functions to retrieve configuration, target repositories, paths, and to ensure required directories exist.
  - Simple JSON‑based persistence helpers (save_config / load_config).

The design mirrors the expectations of the existing codebase:
  * `src.extraction.fetch_prs` expects `get_target_repos()` and `get_paths()` and calls
    `ensure_directories()` (optionally with a list of extra paths).
  * `src.extraction.fetch_human_comments` accesses `paths["annotations"]`, `paths["raw"]`,
    `paths["annotations_raw"]`, etc.
  * Unit tests reference `paths["annotations_raw"]` and `paths["derived_human_confirmations"]`.
All of those keys are now defined.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# ----------------------------------------------------------------------
# Global constants
# ----------------------------------------------------------------------
# Target repositories for PR extraction (required by T002)
TARGET_REPOS: List[str] = [
    "microsoft/vscode",
    "pytorch/pytorch",
    "tensorflow/tensorflow",
]

# Random seed used throughout the pipeline (reproducibility – Constitution I)
RANDOM_SEED: int = 42

# Hyper‑parameters – can be overridden at runtime by tests or the CLI
HYPERPARAMS: Dict[str, Any] = {
    "max_prs": 500,                     # Maximum PRs per repository
    "seed": RANDOM_SEED,
    "thresholds": [0.80, 0.85, 0.90],   # Sensitivity‑analysis thresholds
    "timeout_hours": 6,                 # Global timeout (FR‑013)
}

# ----------------------------------------------------------------------
# Path constants
# ----------------------------------------------------------------------
# Base of the project (the directory that contains this settings.py file)
_BASE_DIR = Path(__file__).resolve().parent.parent

# Directory layout (mirrors the scaffold created by T001)
PATHS: Dict[str, Path] = {
    # Core directories
    "base": _BASE_DIR,
    "data_raw": _BASE_DIR / "data" / "raw",
    "data_derived": _BASE_DIR / "data" / "derived",
    "data_annotations": _BASE_DIR / "data" / "annotations",
    "results": _BASE_DIR / "results",
    "specs": _BASE_DIR / "specs",
    "logs": _BASE_DIR / "logs",

    # Alias keys used by various scripts (kept for backward compatibility)
    "raw": _BASE_DIR / "data" / "raw",
    "derived": _BASE_DIR / "data" / "derived",
    "annotations": _BASE_DIR / "data" / "annotations",
    "raw_data": _BASE_DIR / "data" / "raw",
    "derived_data": _BASE_DIR / "data" / "derived",
    "annotations_raw": _BASE_DIR / "data" / "annotations" / "raw_comments.json",
    "derived_human_confirmations": _BASE_DIR / "data" / "derived" / "human_confirmations.json",
    "derived_human_baseline": _BASE_DIR / "data" / "derived" / "human_baseline.json",
    "derived_llm_detections": _BASE_DIR / "data" / "derived" / "llm_detections.json",
    "raw_prs": _BASE_DIR / "data" / "raw" / "prs.json",
    "raw_checksums": _BASE_DIR / "data" / "raw" / "checksums.json",
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_config() -> Dict[str, Any]:
    """
    Load optional user configuration from ``config/config.json``.
    Returns an empty dict if the file does not exist.
    """
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_target_repos() -> List[str]:
    """
    Return the list of repositories to process.
    Preference order:
      1. ``target_repos`` key in a user‑provided ``config.json``.
      2. The hard‑coded ``TARGET_REPOS`` constant.
    """
    config = get_config()
    return config.get("target_repos", TARGET_REPOS)

def get_paths() -> Dict[str, Path]:
    """
    Return a dictionary mapping symbolic path names to ``pathlib.Path`` objects.
    The dictionary includes both directory roots and convenience file locations.
    """
    return PATHS

def ensure_directories(extra_paths: Optional[List[Path]] = None) -> None:
    """
    Create all required directories if they do not exist.

    Args:
        extra_paths: Optional list of additional ``Path`` objects that callers
                     want to guarantee existence for (e.g. a specific output file
                     directory). The function will create the parent directories
                     of those paths.
    """
    # Create the core directories defined in PATHS
    for key, path in PATHS.items():
        # Only create directories – skip file‑specific entries
        if any(key.endswith(suffix) for suffix in ("_raw", "_derived", "_annotations", "raw", "derived", "annotations", "results", "specs", "logs", "base")):
            path.mkdir(parents=True, exist_ok=True)

    # Handle any extra paths supplied by callers
    if extra_paths:
        for p in extra_paths:
            # If the path points to a file, create its parent directory
            target_dir = p if p.is_dir() else p.parent
            target_dir.mkdir(parents=True, exist_ok=True)

def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """
    Write a configuration dictionary to ``config.json``.
    If ``config_path`` is omitted, the default location next to this module is used.
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load a configuration dictionary from ``config.json``.
    If ``config_path`` is omitted, the default location next to this module is used.
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)