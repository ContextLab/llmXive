"""
Project configuration management for llmXive DomainShuttle pipeline.

This module defines global configuration settings, including paths, seeds,
hyperparameters, and the critical 'fidelity_threshold' used for identity
validation in User Story 3.

Configuration is loaded from environment variables where specified, with
documented default fallbacks. Invalid configurations raise ValueError
immediately to enforce the "FAIL LOUDLY" policy.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional


# --- Project Paths ---
# Base directory is assumed to be the project root relative to this file
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src"
SPECS_DIR = BASE_DIR / "specs"

# Ensure data directories exist
(DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "results").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "figures").mkdir(parents=True, exist_ok=True)


# --- Seeds ---
# Global random seed for reproducibility
RANDOM_SEED: int = int(os.getenv("LMMXIVE_SEED", "42"))


# --- Hyperparameters ---
# Target dimensions for the autoencoder sweep (US2)
TARGET_DIMENSIONS: list[int] = [16, 32, 64, 128, 256]

# Training batch size (CPU-optimized)
BATCH_SIZE: int = 1

# Number of frames to sample per video for complexity/fidelity
NUM_FRAMES_PER_SUBJECT: int = 5

# --- Fidelity Threshold Configuration (T004b) ---
#
# This key defines the minimum CLIP Image Similarity score required to
# consider a compressed video generation as "high fidelity" to the
# original subject.
#
# Default Fallback Mechanism:
#   1. Check environment variable 'LMMXIVE_FIDELITY_THRESHOLD'.
#   2. If not set, use the documented default of 0.75.
#   3. If the value is missing, empty, or cannot be parsed as a float,
#      or if the parsed float is not in the range (0.0, 1.0], raise ValueError.
#
# The threshold is used in src/analysis/fidelity.py to determine the
# minimum dimensionality required for each subject.

FIDELITY_THRESHOLD_ENV_KEY: str = "LMMXIVE_FIDELITY_THRESHOLD"
FIDELITY_THRESHOLD_DEFAULT: float = 0.75

def _load_fidelity_threshold() -> float:
    """
    Load and validate the fidelity threshold configuration.

    Returns:
        float: The validated fidelity threshold value between 0.0 and 1.0.

    Raises:
        ValueError: If the threshold is missing, invalid, or out of range.
    """
    raw_value: Optional[str] = os.getenv(FIDELITY_THRESHOLD_ENV_KEY)

    if raw_value is None or raw_value.strip() == "":
        # Fallback to documented default
        return FIDELITY_THRESHOLD_DEFAULT

    try:
        threshold = float(raw_value)
    except ValueError:
        raise ValueError(
            f"Invalid {FIDELITY_THRESHOLD_ENV_KEY} value: '{raw_value}'. "
            f"Must be a valid float or unset to use default {FIDELITY_THRESHOLD_DEFAULT}."
        )

    if not (0.0 < threshold <= 1.0):
        raise ValueError(
            f"Fidelity threshold must be in the range (0.0, 1.0]. "
            f"Got: {threshold}. Please set {FIDELITY_THRESHOLD_ENV_KEY} to a valid value."
        )

    return threshold


# Load and validate immediately at import time to fail fast
FIDELITY_THRESHOLD: float = _load_fidelity_threshold()


# --- DomainShuttle Specifics ---
GENERATOR_PROMPTS: list[str] = [
    "Anime style",
    "Photorealistic style",
    "Sketch style"
]

# --- Logging Configuration ---
LOG_LEVEL: str = os.getenv("LMMXIVE_LOG_LEVEL", "INFO")

# --- Consolidated Config Dict for easy access ---
CONFIG: Dict[str, Any] = {
    "base_dir": BASE_DIR,
    "data_dir": DATA_DIR,
    "seed": RANDOM_SEED,
    "target_dimensions": TARGET_DIMENSIONS,
    "batch_size": BATCH_SIZE,
    "num_frames": NUM_FRAMES_PER_SUBJECT,
    "fidelity_threshold": FIDELITY_THRESHOLD,
    "prompts": GENERATOR_PROMPTS,
    "log_level": LOG_LEVEL,
}