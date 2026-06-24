"""
Configuration module for the "Evaluating the Impact of Code Duplication on LLM Code Understanding"
project.

This module centralises all reproducibility‑related parameters such as random seeds,
clone‑detection thresholds, and model loading specifications.  Down‑stream code
(e.g., data loading, AST cloning, model inference, correlation analysis, and
visualisation) should import from here rather than hard‑coding values.

The design follows a simple, dependency‑free approach:
* Constants are defined at module level for easy import.
* A ``Config`` dataclass bundles the three logical groups.
* ``get_config()`` returns a singleton instance for convenience.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, List

# ----------------------------------------------------------------------
# Random seeds – ensure reproducibility across the whole pipeline
# ----------------------------------------------------------------------
RANDOM_SEED: int = 42  # Python's ``random`` seed
NUMPY_SEED: int = 42   # NumPy seed (if NumPy is used downstream)
TORCH_SEED: int = 42   # PyTorch seed (for model inference)

# ----------------------------------------------------------------------
# Thresholds – values that control clone detection and sensitivity analysis
# ----------------------------------------------------------------------
# Primary clone‑detection similarity threshold (used by ``ast_cloner``)
CLONE_DETECTION_THRESHOLD: float = 0.8

# Sensitivity‑analysis thresholds for the correlation study (Phase 3, Task T040)
SENSITIVITY_THRESHOLDS: List[float] = [0.7, 0.8, 0.9]

# ----------------------------------------------------------------------
# Model parameters – specifications for loading the LLM used for perplexity
# ----------------------------------------------------------------------
MODEL_PARAMS: Dict[str, str] = {
    "model_name": "Salesforce/codegen-350M-mono",
    # Quantisation strategy – bitsandbytes 8‑bit is the default for this project
    "quantization": "bitsandbytes_8bit",
    # Device selection – overridden by environment variable if needed
    "device": "cuda",
}

# ----------------------------------------------------------------------
# Dataclass that groups the above values – convenient for passing around
# ----------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class Config:
    """Immutable configuration container."""

    random_seed: int = RANDOM_SEED
    numpy_seed: int = NUMPY_SEED
    torch_seed: int = TORCH_SEED

    clone_detection_threshold: float = CLONE_DETECTION_THRESHOLD
    sensitivity_thresholds: List[float] = dataclasses.field(
        default_factory=lambda: SENSITIVITY_THRESHOLDS
    )

    model_params: Dict[str, str] = dataclasses.field(
        default_factory=lambda: MODEL_PARAMS
    )

# A module‑level singleton – most code will simply import ``CONFIG``
CONFIG = Config()

def get_config() -> Config:
    """
    Return the global immutable configuration instance.

    The function exists primarily for type‑checkers and for code that prefers a
    callable over a module‑level constant.
    """
    return CONFIG

__all__ = [
    "RANDOM_SEED",
    "NUMPY_SEED",
    "TORCH_SEED",
    "CLONE_DETECTION_THRESHOLD",
    "SENSITIVITY_THRESHOLDS",
    "MODEL_PARAMS",
    "Config",
    "CONFIG",
    "get_config",
]