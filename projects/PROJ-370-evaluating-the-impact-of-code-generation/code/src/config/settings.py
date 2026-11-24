"""
Central configuration module (Task T002, FR-001).

Defines:
- ``TARGET_REPOS``: the GitHub repositories to analyse.
- ``HYPERPARAMS``: all pipeline hyper-parameters (thresholds, limits,
  model settings, statistical parameters).
- Path constants and helpers (``get_paths``, ``ensure_directories``).
- Random seeds for reproducibility.
- JSON config load/save helpers.

This module is the single source of truth for configuration; the
legacy ``code/config/settings.py`` re-exports everything from here so
that both ``code.config.settings`` and ``code.src.config.settings``
expose the same API.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Project layout
# ---------------------------------------------------------------------------
# This file lives at <project_root>/code/src/config/settings.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]

PATHS: Dict[str, Path] = {
    "project_root": PROJECT_ROOT,
    "data": PROJECT_ROOT / "data",
    "data_raw": PROJECT_ROOT / "data" / "raw",
    "data_annotations": PROJECT_ROOT / "data" / "annotations",
    "data_derived": PROJECT_ROOT / "data" / "derived",
    "data_results": PROJECT_ROOT / "data" / "results",
    "data_validation": PROJECT_ROOT / "data" / "validation",
    "logs": PROJECT_ROOT / "logs",
    "results": PROJECT_ROOT / "results",
    "contracts": PROJECT_ROOT
    / "specs"
    / "001-eval-llm-review-quality"
    / "contracts",
    "config": PROJECT_ROOT / "config",
}

DEFAULT_CONFIG_PATH = PATHS["config"] / "config.json"

# ---------------------------------------------------------------------------
# Target repositories (FR-001)
# ---------------------------------------------------------------------------
TARGET_REPOS: List[str] = [
    "microsoft/vscode",
    "pytorch/pytorch",
    "tensorflow/tensorflow",
]

# ---------------------------------------------------------------------------
# Reproducibility: random seeds
# ---------------------------------------------------------------------------
RANDOM_SEED: int = 42
NUMPY_SEED: int = 42
PYTHON_SEED: int = 42

# ---------------------------------------------------------------------------
# Hyper-parameters
# ---------------------------------------------------------------------------
HYPERPARAMS: Dict[str, Any] = {
    # Data extraction (FR-001)
    "max_prs": 500,
    "prs_per_page": 100,
    # LLM inference (FR-002, FR-015)
    "llm_model_name": "bigcode/starcoder2-3b",
    "llm_dtype": "float16",
    "llm_low_cpu_mem_usage": True,
    "llm_device": "cpu",
    "max_diff_tokens": 8000,
    "per_pr_latency_seconds": 300,      # 5 minutes (FR-015)
    "json_parse_retries": 2,
    "retry_delay_seconds": 1.0,
    # Alignment (FR-003, FR-012)
    "similarity_threshold": 0.85,
    "sensitivity_thresholds": [0.80, 0.85, 0.90],
    "line_jaccard_min_overlap": 0.5,
    "line_tolerance": 5,
    # Ground truth (FR-011)
    "min_independent_reviewers": 2,
    "min_verified_prs": 50,
    "manual_validation_size": 20,
    # Runtime guard (FR-013)
    "global_deadline_seconds": 21600,   # 6 hours
    "sample_cap": 200,
    "max_memory_gb": 7,
    # Statistics
    "alpha": 0.05,
    "severity_labels": ["critical", "major", "minor", "style"],
}


def get_paths() -> Dict[str, str]:
    """Return a mapping of logical names to absolute path strings."""
    return {name: str(path) for name, path in PATHS.items()}


def ensure_directories(extra_paths: Optional[List[Path]] = None) -> None:
    """Create all directories in ``PATHS`` plus any ``extra_paths``.

    Idempotent: existing directories are left untouched.
    """
    for path in PATHS.values():
        Path(path).mkdir(parents=True, exist_ok=True)
    for path in extra_paths or []:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)


def get_target_repos() -> List[str]:
    """Return the list of GitHub repositories to process.

    Precedence: JSON config file > ``GITHUB_TARGET_REPOS`` environment
    variable > module-level ``TARGET_REPOS`` constant.
    """
    config = get_config()
    repos = config.get("target_repos")
    if repos:
        return list(repos)
    env_repos = os.getenv("GITHUB_TARGET_REPOS")
    if env_repos:
        return [r.strip() for r in env_repos.split(",") if r.strip()]
    return list(TARGET_REPOS)


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load a JSON configuration file (empty dict if it does not exist)."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Config file {path} must contain a JSON object")
    return data


def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """Write a configuration dictionary to JSON."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False, sort_keys=True)


def get_config() -> Dict[str, Any]:
    """Convenience wrapper that loads the default configuration file."""
    return load_config()


def get_hyperparams() -> Dict[str, Any]:
    """Return the effective hyper-parameters (config overrides defaults)."""
    effective = dict(HYPERPARAMS)
    effective.update(get_config().get("hyperparams", {}))
    return effective


def get_seed() -> int:
    """Return the effective random seed (config may override)."""
    return int(get_config().get("seed", RANDOM_SEED))
