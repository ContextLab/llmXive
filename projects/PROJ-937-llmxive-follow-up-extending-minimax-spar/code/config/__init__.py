"""
Configuration management for llmXive follow-up: extending MiniMax Sparse Attention.

This module handles environment variable management for:
- Model paths (MiniMax-M3 GGUF)
- RULER dataset cache locations
- Resource constraints (CPU-only enforcement)
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_ROOT = _PROJECT_ROOT / "state"

# Environment variable keys
ENV_MODEL_PATH = "MINIMAX_MODEL_PATH"
ENV_RULER_CACHE = "RULER_CACHE_DIR"
ENV_CPU_ONLY = "LLMXIVE_CPU_ONLY"
ENV_LOG_LEVEL = "LLMXIVE_LOG_LEVEL"

# Defaults
DEFAULT_MODEL_PATH = "MiniMaxAI/MiniMax-M3"
DEFAULT_RULER_CACHE = str(_PROJECT_ROOT / "data" / "raw" / "ruler")
DEFAULT_CPU_ONLY = "true"  # Enforce CPU-only by default per task requirements
DEFAULT_LOG_LEVEL = "INFO"


def get_model_path() -> str:
    """
    Retrieve the path to the MiniMax-M3 model.

    Priority:
    1. Environment variable MINIMAX_MODEL_PATH
    2. Default: 'MiniMaxAI/MiniMax-M3' (used by MiniMaxWrapper to locate GGUF)

    Returns:
        str: The resolved model path.
    """
    return os.environ.get(ENV_MODEL_PATH, DEFAULT_MODEL_PATH)


def get_ruler_cache_dir() -> Path:
    """
    Retrieve the directory for caching the RULER benchmark dataset.

    Priority:
    1. Environment variable RULER_CACHE_DIR
    2. Default: <project_root>/data/raw/ruler

    Returns:
        Path: The absolute path to the cache directory.
    """
    raw_path = os.environ.get(ENV_RULER_CACHE, DEFAULT_RULER_CACHE)
    return Path(raw_path).resolve()


def is_cpu_only() -> bool:
    """
    Check if the system is configured to run CPU-only.

    Returns:
        bool: True if CPU_ONLY is set to 'true' (case-insensitive), False otherwise.
    """
    val = os.environ.get(ENV_CPU_ONLY, DEFAULT_CPU_ONLY)
    return val.lower() in ("true", "1", "yes")


def get_log_level() -> str:
    """
    Retrieve the logging level from environment.

    Returns:
        str: The logging level string (e.g., 'INFO', 'DEBUG').
    """
    return os.environ.get(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL)


def ensure_config_dirs() -> Dict[str, Path]:
    """
    Ensure all necessary configuration and data directories exist.
    Creates directories for model cache, ruler cache, and state if missing.

    Returns:
        Dict[str, Path]: Mapping of directory names to their resolved paths.
    """
    ruler_dir = get_ruler_cache_dir()
    ruler_dir.mkdir(parents=True, exist_ok=True)

    # Ensure state directory exists for checksum recording
    _CONFIG_ROOT.mkdir(parents=True, exist_ok=True)

    return {
        "ruler_cache": ruler_dir,
        "config_root": _CONFIG_ROOT,
    }


def get_config_summary() -> Dict[str, Any]:
    """
    Generate a summary of the current configuration state.

    Returns:
        Dict[str, Any]: A dictionary containing current config values.
    """
    return {
        "model_path": get_model_path(),
        "ruler_cache": str(get_ruler_cache_dir()),
        "cpu_only": is_cpu_only(),
        "log_level": get_log_level(),
        "project_root": str(_PROJECT_ROOT),
    }


# Initialize directories on import to ensure readiness
# This is safe as it uses mkdir(exist_ok=True)
_dirs = ensure_config_dirs()