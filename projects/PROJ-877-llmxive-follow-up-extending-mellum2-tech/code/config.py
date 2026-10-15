"""
Configuration management module for the llmXive pipeline.
Handles environment variables, project root detection, seed setting,
and provides project-wide constants.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

# External dependencies (provided by the llmXive platform)
from llmxive_toolkit import paths  # Provides project-wide path helpers

# ----------------------------------------------------------------------
# Primary constants required by the specification
# ----------------------------------------------------------------------
# Fixed random seed for reproducibility across the entire pipeline
SEED: int = 12345

# Identifier of the primary frozen LLM to be used for inference.
# Accepted values per spec: "Mistral-7B" or "Llama-3-8B".
PRIMARY_MODEL_ID: str = "Mistral-7B"

# HuggingFace Hub identifier for the primary frozen model.
PRIMARY_MODEL_HF_ID: str = "mistralai/Mistral-7B-v0.1"

# ----------------------------------------------------------------------
# Environment variable handling
# ----------------------------------------------------------------------
# Optional environment variables; none are strictly required at import
# time so that `python -c "import code.config"` always succeeds.
OPTIONAL_ENV_VARS: List[str] = [
    "HF_TOKEN",
    "HF_DATASET_NAME",
    "MAX_WORKERS",
    "TIMEOUT_SECONDS",
    "RANDOM_SEED",
    "BATCH_SIZE",
    "DEVICE",
]


def get_project_root() -> Path:
    """
    Determine the absolute path to the project root.

    Returns:
        Path: Absolute path to the repository root.
    """
    root_env = os.getenv("PROJECT_ROOT")
    if root_env:
        return Path(root_env).resolve()

    # Fallback: assume this file lives in <project_root>/code/config.py
    current_file = Path(__file__).resolve()
    if current_file.parent.name == "code":
        return current_file.parent.parent
    return Path.cwd()


def load_environment() -> Dict[str, str]:
    """
    Return a copy of the current environment variables.

    Returns:
        dict: Mapping of environment variable names to values.
    """
    return dict(os.environ)


def get_config() -> Dict[str, Any]:
    """
    Assemble the configuration dictionary from environment variables,
    applying documented defaults for any that are absent.

    Returns:
        dict: Configuration values used throughout the pipeline.
    """
    return {
        "project_root": str(get_project_root()),
        "hf_token": os.getenv("HF_TOKEN", ""),
        "hf_dataset_name": os.getenv("HF_DATASET_NAME", "codeparrot/github-code"),
        "max_workers": int(os.getenv("MAX_WORKERS", "4")),
        "timeout_seconds": int(os.getenv("TIMEOUT_SECONDS", "300")),
        "seed": int(os.getenv("RANDOM_SEED", str(SEED))),
        "batch_size": int(os.getenv("BATCH_SIZE", "1")),
        "device": os.getenv("DEVICE", "cpu"),
        # Primary model identifier is part of the spec and exposed here
        "primary_model_id": PRIMARY_MODEL_ID,
        "primary_model_hf_id": PRIMARY_MODEL_HF_ID,
    }


def set_seed(seed: Optional[int] = None) -> None:
    """
    Seed the Python, NumPy, and (if available) PyTorch RNGs for reproducibility.

    Args:
        seed: Desired seed value. If None, defaults to the value from
              get_config() or the module-level SEED constant.
    """
    if seed is None:
        seed = get_config().get("seed", SEED)
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


# ----------------------------------------------------------------------
# Project-wide path helpers (thin wrappers around llmxive_toolkit.paths)
# ----------------------------------------------------------------------
# These helpers expose the same API as the toolkit but make the intent
# explicit within this config module.
def data_path(*segments: str) -> Path:
    """Return a Path under the project's data directory, creating parents."""
    return paths.data(*segments)


def figures_path(*segments: str) -> Path:
    """Return a Path under the project's figures directory, creating parents."""
    return paths.figures(*segments)


def results_path(*segments: str) -> Path:
    """Return a Path under the project's results directory, creating parents."""
    return paths.results(*segments)


def docs_path(*segments: str) -> Path:
    """Return a Path under the project's docs directory, creating parents."""
    return paths.docs(*segments)


# ----------------------------------------------------------------------
# CLI entry point for quick validation of the configuration module
# ----------------------------------------------------------------------
def main() -> int:
    """
    Simple sanity-check that the configuration can be loaded without errors.

    Returns:
        int: Exit status (0 = success, 1 = failure).
    """
    try:
        cfg = get_config()
        print("Configuration loaded successfully:")
        for k, v in cfg.items():
            # Mask tokens for safety
            if "token" in k.lower() or "secret" in k.lower():
                v = "***"
            print(f"  {k}: {v}")
        return 0
    except Exception as e:
        print(f"Configuration error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
