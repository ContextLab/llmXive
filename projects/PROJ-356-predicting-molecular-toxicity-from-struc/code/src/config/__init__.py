"""
Configuration management package for the molecular toxicity pipeline.

Provides centralized, environment-variable-driven path management so that
every pipeline stage resolves directories (data, results, models, config,
state, docs) through a single source of truth.

Environment variables (all optional; defaults resolve relative to the
project code directory):
    TOXICITY_PROJECT_DIR   - root of the project tree (contains code/)
    TOXICITY_DATA_DIR      - raw/processed data directory
    TOXICITY_RAW_DATA_DIR  - raw data directory
    TOXICITY_PROCESSED_DATA_DIR - processed data directory
    TOXICITY_RESULTS_DIR   - results/report directory
    TOXICITY_MODELS_DIR    - saved model artifacts directory
    TOXICITY_CONFIG_DIR    - configuration directory
    TOXICITY_STATE_DIR     - state file directory
    TOXICITY_DOCS_DIR      - documentation directory

Usage:
    from src.config import get_paths

    paths = get_paths()
    raw_csv = paths["data_raw"] / "toxcast.csv"
"""

import os
from pathlib import Path
from typing import Dict, List

__all__ = [
    "PROJECT_CODE_DIR",
    "ENV_VAR_MAP",
    "get_project_dir",
    "get_paths",
    "get_path",
    "resolve_path",
    "ensure_directories",
    "get_alerts_config_path",
    "get_alerts_schema_path",
]

# This file lives at <project>/code/src/config/__init__.py
PROJECT_CODE_DIR = Path(__file__).resolve().parents[2]

# Mapping of logical path names to environment variable overrides.
ENV_VAR_MAP: Dict[str, str] = {
    "project": "TOXICITY_PROJECT_DIR",
    "data": "TOXICITY_DATA_DIR",
    "data_raw": "TOXICITY_RAW_DATA_DIR",
    "data_processed": "TOXICITY_PROCESSED_DATA_DIR",
    "results": "TOXICITY_RESULTS_DIR",
    "models": "TOXICITY_MODELS_DIR",
    "config": "TOXICITY_CONFIG_DIR",
    "state": "TOXICITY_STATE_DIR",
    "docs": "TOXICITY_DOCS_DIR",
}

# Default relative locations (relative to the project root, i.e. the
# parent of code/). If the project root itself is overridden, data
# subdirectories hang off the code/ directory by default.
_DEFAULT_RELATIVE: Dict[str, str] = {
    "data": "data",
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "results": "results",
    "models": "models",
    "config": "config",
    "state": "state",
    "docs": "docs",
}


def get_project_dir() -> Path:
    """Return the project root directory.

    Respects the TOXICITY_PROJECT_DIR environment variable; otherwise
    defaults to the parent of the code/ directory containing this
    package.
    """
    env = os.environ.get(ENV_VAR_MAP["project"])
    if env:
        return Path(env).expanduser().resolve()
    return PROJECT_CODE_DIR


def get_paths() -> Dict[str, Path]:
    """Resolve all standard pipeline directories.

    Returns a dictionary with keys: project, code, data, data_raw,
    data_processed, results, models, config, state, docs. Each value is
    an absolute Path. Environment variables take precedence over the
    default locations.
    """
    project = get_project_dir()
    paths: Dict[str, Path] = {
        "project": project,
        "code": PROJECT_CODE_DIR,
    }
    for name, env_var in ENV_VAR_MAP.items():
        if name == "project":
            continue
        env_value = os.environ.get(env_var)
        if env_value:
            paths[name] = Path(env_value).expanduser().resolve()
        else:
            paths[name] = (PROJECT_CODE_DIR / _DEFAULT_RELATIVE[name]).resolve()
    return paths


def get_path(name: str) -> Path:
    """Resolve a single named path (e.g. 'data_raw', 'results').

    Raises:
        KeyError: if the name is not a recognized path key.
    """
    paths = get_paths()
    if name not in paths:
        raise KeyError(
            f"Unknown path name '{name}'. Valid names: {sorted(paths.keys())}"
        )
    return paths[name]


def resolve_path(name: str, *parts: str) -> Path:
    """Resolve a named directory and join additional path components.

    Example:
        resolve_path("data_raw", "toxcast.csv")
            -> <code>/data/raw/toxcast.csv
    """
    return get_path(name).joinpath(*parts)


def ensure_directories(names: List[str]) -> Dict[str, Path]:
    """Create the named directories if they do not exist.

    Args:
        names: list of path names from ENV_VAR_MAP (e.g. ['data_raw',
            'results']).

    Returns:
        Dictionary of the created/verified directory paths.
    """
    created: Dict[str, Path] = {}
    for name in names:
        p = get_path(name)
        p.mkdir(parents=True, exist_ok=True)
        created[name] = p
    return created


def get_alerts_config_path() -> Path:
    """Return the path to the curated structural alerts JSON config."""
    env = os.environ.get("TOXICITY_ALERTS_CONFIG")
    if env:
        return Path(env).expanduser().resolve()
    return get_path("config") / "structural_alerts.json"


def get_alerts_schema_path() -> Path:
    """Return the path to the alerts JSON Schema contract."""
    env = os.environ.get("TOXICITY_ALERTS_SCHEMA")
    if env:
        return Path(env).expanduser().resolve()
    return (
        get_path("code")
        / "specs"
        / "001-predicting-molecular-toxicity-from-struc"
        / "contracts"
        / "alerts.schema.yaml"
    )
