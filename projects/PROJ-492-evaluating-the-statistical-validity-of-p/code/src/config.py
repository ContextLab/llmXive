"""
Configuration constants for the A/B Test Validity Audit Pipeline.

This module defines deterministic seeds, statistical thresholds, and resource
caps required for reproducibility and compliance with Constitution Principle I.

All Random Number Generators (RNGs) used in the pipeline must be seeded via
`set_rng_seed()` at startup to ensure deterministic behavior.
"""

import random
import os
from typing import Optional, Dict, Any
import numpy as np

# ==============================================================================
# Core Reproducibility Constants (Constitution Principle I)
# ==============================================================================

SEED: int = 42
"""Deterministic random seed for all RNGs to ensure reproducibility."""

# ==============================================================================
# Statistical Thresholds (FR-004, FR-012)
# ==============================================================================

P_VALUE_THRESHOLD: float = 0.05
"""Standard significance threshold for p-values."""

ABSOLUTE_P_DIFFERENCE_THRESHOLD: float = 0.05
"""Threshold for absolute difference between reported and reconstructed p-values."""

RELATIVE_EFFECT_SIZE_THRESHOLD: float = 0.05
"""Threshold for relative difference in effect sizes (5%)."""

MIN_SAMPLE_SIZE: int = 30
"""Minimum sample size required for valid statistical inference (rule of thumb)."""

CORRECTION_FACTOR: float = 1.0
"""Factor for adjusting thresholds if needed (currently 1.0)."""

# ==============================================================================
# Resource Caps (FR-009, SC-008)
# ==============================================================================

MAX_RAM_GB: float = 2.0
"""Maximum allowed RAM usage in Gigabytes."""

MAX_CPU_CORES: int = 2
"""Maximum allowed CPU cores."""

TIMEOUT_SECONDS: int = 3600
"""Default timeout for pipeline steps in seconds (1 hour)."""

# ==============================================================================
# Monte Carlo Validation Parameters (FR-026)
# ==============================================================================

MONTE_CARLO_REPLICATES: int = 10000
"""Number of replicates for Monte Carlo validation."""

MONTE_CARLO_TOLERANCE: float = 0.005
"""Maximum allowed absolute difference between Monte Carlo and library p-values."""

# ==============================================================================
# Subgroup Analysis Parameters (FR-032)
# ==============================================================================

MIN_SUBGROUP_SIZE: int = 10
"""Minimum number of summaries required for a subgroup to be analyzed."""

BONFERRONI_ALPHA: float = 0.05
"""Base alpha for Bonferroni correction."""

# ==============================================================================
# File Paths (Relative to project root)
# ==============================================================================

DATA_DIR: str = "data"
OUTPUT_DIR: str = "output"
LOGS_DIR: str = "logs"
CONFIG_FILE: str = "config.yaml"

# ==============================================================================
# RNG Seeding Functions
# ==============================================================================

def set_rng_seed(seed: Optional[int] = None) -> None:
    """
    Initialize all Random Number Generators with a deterministic seed.

    This function must be called at the entry point of any script or module
    that performs stochastic operations to ensure reproducibility (Constitution
    Principle I).

    Args:
        seed: The seed value. If None, defaults to config.SEED.
    """
    if seed is None:
        seed = SEED

    # Seed Python's built-in random module
    random.seed(seed)

    # Seed NumPy's random number generator
    np.random.seed(seed)

    # Note: If using torch or tensorflow, they would be seeded here as well.
    # For this project, we rely on standard library, numpy, and scipy.

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a summary of the current configuration state.

    Useful for logging and provenance tracking.

    Returns:
        A dictionary containing key configuration values.
    """
    return {
        "seed": SEED,
        "p_value_threshold": P_VALUE_THRESHOLD,
        "absolute_p_diff_threshold": ABSOLUTE_P_DIFFERENCE_THRESHOLD,
        "relative_effect_size_threshold": RELATIVE_EFFECT_SIZE_THRESHOLD,
        "max_ram_gb": MAX_RAM_GB,
        "max_cpu_cores": MAX_CPU_CORES,
        "monte_carlo_replicates": MONTE_CARLO_REPLICATES,
        "monte_carlo_tolerance": MONTE_CARLO_TOLERANCE,
        "min_subgroup_size": MIN_SUBGROUP_SIZE,
    }
