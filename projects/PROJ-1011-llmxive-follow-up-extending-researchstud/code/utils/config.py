"""
Configuration utilities for the llmXive research pipeline.

This module provides functions to set random seeds for reproducibility
across NumPy, Python's random module, and PyTorch (if installed). It also
loads model configuration information and provides a deterministic hash
of the environment.

On import, the default seed is applied automatically so that any module
importing ``config`` inherits the seeded state.
"""
import os
import random
import hashlib
import json
import logging
from typing import Optional, Dict, Any, Tuple, List

import numpy as np
import yaml
from pathlib import Path

from utils.logging_config import get_logger, ensure_log_dir

logger = get_logger("config")

# ----------------------------------------------------------------------
# Default seed used for the entire pipeline. Adjust if a different
# deterministic seed is required.
# ----------------------------------------------------------------------
DEFAULT_SEED: int = 42

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Sets the random seed for reproducibility across numpy, python random,
    and torch (if available).

    Parameters
    ----------
    seed : int, optional
        The seed value to set. Defaults to ``DEFAULT_SEED`` (42).
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        logger.debug("PyTorch not found, skipping torch seed setting.")

    logger.info(f"Seed set to {seed}")

# Apply the default seed automatically when this module is imported.
set_seed(DEFAULT_SEED)

def get_environment_hash() -> str:
    """
    Generates a hash of the current environment configuration for
    reproducibility tracking.

    Returns
    -------
    str
        SHA‑256 hash representing the environment variables of interest.
    """
    env_vars = {
        "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED", ""),
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
    }
    data = json.dumps(env_vars, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()

def validate_seed(seed: int) -> bool:
    """
    Validates that the seed is a non‑negative integer.

    Parameters
    ----------
    seed : int
        Seed value to validate.

    Returns
    -------
    bool
        ``True`` if ``seed`` is a non‑negative integer, ``False`` otherwise.
    """
    return isinstance(seed, int) and seed >= 0

def get_model_config() -> Dict[str, Any]:
    """
    Loads model configuration from ``data-sources.yaml`` or falls back to
    sensible defaults.

    Returns
    -------
    dict
        Dictionary containing model settings such as primary/fallback model
        names and similarity thresholds.
    """
    config_path = Path("data-sources.yaml")
    if not config_path.exists():
        logger.warning("data-sources.yaml not found. Using defaults.")
        return {
            "primary_model": "all-MiniLM-L6-v2",
            "fallback_model": "paraphrase-MiniLM-L3-v2",
            "similarity_threshold": 0.5,
            "top_k_patterns": 3,
        }

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        # Extract the model sub‑section if present.
        model_config = data.get("model_config", {})
        defaults = {
            "primary_model": "all-MiniLM-L6-v2",
            "fallback_model": "paraphrase-MiniLM-L3-v2",
            "similarity_threshold": 0.5,
            "top_k_patterns": 3,
        }
        return {**defaults, **model_config}
    except Exception as e:
        logger.error(f"Error loading model config: {e}")
        return {
            "primary_model": "all-MiniLM-L6-v2",
            "fallback_model": "paraphrase-MiniLM-L3-v2",
            "similarity_threshold": 0.5,
            "top_k_patterns": 3,
        }

def select_model_on_memory_error(primary_model: str, fallback_model: str) -> str:
    """
    Chooses a fallback model when a memory error occurs during loading.

    Parameters
    ----------
    primary_model : str
        Name of the primary model that failed to load.
    fallback_model : str
        Name of the fallback model to use instead.

    Returns
    -------
    str
        The name of the fallback model.
    """
    logger.warning(
        f"Memory error on {primary_model}. Selecting fallback model {fallback_model}."
    )
    return fallback_model
