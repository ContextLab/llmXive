"""
Minimal configuration utilities for the evaluation pipeline.

This module provides a simple ``get_config`` function that loads
optional configuration from a ``config.yaml`` file (if present) and
falls back to sensible defaults.  It also defines a few constants
used throughout the pipeline, such as the maximum allowed runtime
and the canonical path for the runtime report.

The original implementation required a ``GITHUB_TOKEN`` environment
variable and raised an ``EnvironmentError`` if it was missing.  For
the purposes of the runtime instrumentation task (T014) we make the
token optional – the pipeline can operate without it, and downstream
stages that need the token can handle the ``None`` value explicitly.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict

from llmxive_toolkit import paths

# ------------------------------------------------------------------
# Constants used by the pipeline
# ------------------------------------------------------------------
# Path where the runtime report will be written (can be overridden)
RUNTIME_REPORT_PATH = paths.data("processed", "runtime_report.json")

# Upper bound on total pipeline runtime in seconds (6 hours)
MAX_RUNTIME_SECONDS = 21_600

# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------
def _load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """Load a YAML configuration file if it exists."""
    try:
        import yaml  # PyYAML is part of the base environment
    except Exception as exc:
        raise RuntimeError("PyYAML is required to load config files") from exc

    if not file_path.is_file():
        return {}
    with file_path.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp) or {}

def get_config() -> Dict[str, Any]:
    """
    Load pipeline configuration.

    The function looks for a ``config.yaml`` file in the project root.
    If the file does not exist, a minimal configuration dictionary is
    returned.  The configuration may contain arbitrary keys required
    by downstream modules (e.g. ``seed`` for reproducibility).

    Returns
    -------
    dict
        Configuration dictionary.
    """
    project_root = Path(__file__).resolve().parents[2]  # <project>/code/utils/
    config_path = project_root / "config.yaml"
    config = _load_yaml_config(config_path)

    # Ensure a deterministic random seed is always available.
    if "seed" not in config:
        config["seed"] = 42

    # ``GITHUB_TOKEN`` is optional – downstream code can decide what to do.
    config["github_token"] = os.getenv("GITHUB_TOKEN")

    return config

def ensure_directories(paths_list):
    """
    Ensure that each path in ``paths_list`` exists as a directory.

    Parameters
    ----------
    paths_list : list[str | pathlib.Path]
        List of directory paths to create if they do not already exist.
    """
    for p in paths_list:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
