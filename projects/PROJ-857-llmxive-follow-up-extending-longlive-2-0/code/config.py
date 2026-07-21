"""
Configuration constants and path utilities for the llmXive project.
"""
import os
import sys
from pathlib import Path
from typing import Final, List, Dict, Any, Optional

# Project Root
# Assumes code/ is at projects/PROJ-857-llmxive-follow-up-extending-longlive-2-0/code/
# We traverse up to find the project root dynamically or use a fixed relative structure.
# Based on task description, root is the parent of 'code', 'data', 'tests', 'specs'.
_CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _CURRENT_DIR.parent

# --- Bit-width Constants ---
# Supported bit-widths for NVFP4 emulation and analysis
SUPPORTED_BIT_WIDTHS: Final[List[int]] = [2, 3, 4, 5, 6]
DEFAULT_BIT_WIDTH: Final[int] = 4

# --- Seed Constants ---
# Fixed seeds for reproducibility across experiments
BASE_SEED: Final[int] = 42
SEEDS_FOR_EXPERIMENTS: Final[List[int]] = [42, 123, 456, 789, 1011]

# --- Memory & Resource Constraints ---
MAX_RAM_GB: Final[float] = 7.0
MAX_DISK_GB: Final[float] = 14.0
CLIP_DURATION_SECONDS: Final[int] = 4
MAX_CLIPS_PER_RUN: Final[int] = 100  # Safety limit for local runs

# --- Path Configuration ---
# Relative paths from PROJECT_ROOT
PATHS: Final[Dict[str, str]] = {
    "data": "data",
    "data_external": "data/external",
    "data_derived": "data/derived",
    "data_results": "data/results",
    "code": "code",
    "tests": "tests",
    "specs": "specs",
    "figures": "figures",
    "simulation": "simulation",
    "evaluation": "evaluation",
    "analysis": "analysis",
}

# --- Dataset Specifics ---
DATASET_NAME: Final[str] = "kinetics-400"
DATASET_SPLIT: Final[str] = "train"
CLIP_FRAMES_PER_SECOND: Final[int] = 8
CLIP_TOTAL_FRAMES: Final[int] = CLIP_FRAMES_PER_SECOND * CLIP_DURATION_SECONDS  # 32 frames

# --- Evaluation Constants ---
CLIP_MODEL_NAME: Final[str] = "openai/clip-vit-base-patch32"
MAX_CLIPS_FOR_EVALUATION: Final[int] = 50
CORRELATION_THRESHOLD_FR007: Final[float] = 0.7

# --- Simulation Constants ---
STABILITY_THRESHOLD: Final[float] = 1e-6
MAX_EPOCHS: Final[int] = 10
LEARNING_RATE: Final[float] = 1e-4


def get_path_str(key: str) -> str:
    """
    Retrieve the absolute string path for a given configuration key.

    Args:
        key (str): The key defined in the PATHS dictionary (e.g., 'data', 'data_results').

    Returns:
        str: Absolute path string.

    Raises:
        KeyError: If the key is not found in PATHS.
    """
    if key not in PATHS:
        raise KeyError(f"Path key '{key}' not found in configuration.")
    return str(PROJECT_ROOT / PATHS[key])


def ensure_dirs_exist(keys: Optional[List[str]] = None) -> None:
    """
    Ensure that directories corresponding to the given keys exist.
    If keys is None, creates all directories defined in PATHS.

    Args:
        keys (Optional[List[str]]): List of path keys to ensure.
    """
    dirs_to_create = keys if keys is not None else list(PATHS.keys())
    for key in dirs_to_create:
        dir_path = Path(get_path_str(key))
        dir_path.mkdir(parents=True, exist_ok=True)