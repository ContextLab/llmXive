"""
Configuration constants for the A/B Test Audit Pipeline.

This module defines all deterministic seeds, statistical thresholds,
and resource caps used throughout the pipeline. Per Constitution
Principle I, all random number generators must be seeded using the
SEED value defined here at module startup.

Import pattern for other modules:
    from code.src.config import SEED, set_rng_seed

    # At startup of any module using RNGs:
    set_rng_seed()
"""

import random
import os
from typing import Optional

# =============================================================================
# Random Seed Configuration (Constitution Principle I)
# =============================================================================

SEED: int = 42
"""Deterministic random seed for all stochastic operations.

This seed ensures reproducibility across all pipeline runs.
All modules using random number generators MUST seed their RNGs
using set_rng_seed() at startup.
"""

# =============================================================================
# Statistical Thresholds (FR-004, FR-012)
# =============================================================================

P_VALUE_THRESHOLD: float = 0.05
"""Threshold for p-value discrepancy detection.

Absolute p-value difference > 0.05 triggers inconsistency flag.
"""

EFFECT_SIZE_THRESHOLD: float = 0.05
"""Threshold for effect size discrepancy detection.

Relative effect size difference > 5% triggers inconsistency flag.
"""

SAMPLE_SIZE_MINIMUM: int = 300
"""Minimum audited corpus size per FR-025.

Power analysis requires N >= 300 or N >= calculated_minimum.
"""

MIN_SUBGROUP_SIZE: int = 10
"""Minimum summaries required for subgroup analysis (FR-032).

Fisher's exact test applied only to groups with >= 10 summaries.
"""

MAX_DOMAIN_PROPORTION: float = 0.30
"""Maximum allowed proportion for any single domain (FR-027).

If a domain exceeds 30%, bias adjustment or subsampling is triggered.
"""

P_VALUE_CUTOFF: float = 0.05
"""Default p-value cutoff for statistical significance.

Used for binomial prevalence tests and Fisher's exact tests.
"""

# =============================================================================
# Resource Caps (FR-009, SC-008)
# =============================================================================

MAX_CPU_VCPUS: int = 2
"""Maximum CPU vCPUs for CI execution.

Pipeline must complete within 2 vCPU limit.
"""

MAX_RAM_GB: float = 2.0
"""Maximum RAM in GB for CI execution.

Pipeline must not exceed 2 GB memory usage.
"""

MAX_RUNTIME_HOURS: float = 6.0
"""Maximum runtime in hours for CI execution.

Full pipeline must complete within 6 hours.
"""

MAX_URLS_PER_RUN: int = 1000
"""Maximum number of URLs to process per pipeline run.

Prevents excessive resource consumption on large corpora.
"""

# =============================================================================
# File and Path Configuration
# =============================================================================

DATA_DIR: str = "data"
"""Base directory for data artifacts."""

OUTPUT_DIR: str = "output"
"""Base directory for output artifacts."""

CONTRACTS_DIR: str = "contracts"
"""Base directory for JSON schema contracts."""

LOG_FILE: str = "pipeline.log"
"""Default log file name."""

MANIFEST_FILE: str = "manifest.json"
"""Manifest file for artifact checksums."""

PROVENANCE_LOG: str = "provenance_log.csv"
"""Provenance tracking log file."""

# =============================================================================
# Error Code Ranges (FR-007)
# =============================================================================

ERROR_CODE_RANGE_START: int = 0
"""Start of error code range."""

ERROR_CODE_RANGE_END: int = 999
"""End of error code range."""

# =============================================================================
# Monte Carlo Configuration (FR-026)
# =============================================================================

MONTE_CARLO_REPLICATES: int = 10000
"""Number of Monte Carlo replicates for validation."""

MONTE_CARLO_TOLERANCE: float = 0.005
"""Maximum acceptable difference between Monte Carlo and library results."""

# =============================================================================
# RNG Seeding Utility
# =============================================================================

def set_rng_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for all Python RNGs.

    Per Constitution Principle I, all stochastic operations must use
    deterministic seeds for reproducibility. Call this function at
    the startup of any module that uses random number generators.

    Args:
        seed: Optional seed value. Defaults to SEED constant if None.
    """
    if seed is None:
        seed = SEED

    # Seed Python's built-in random module
    random.seed(seed)

    # Seed numpy if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    # Seed torch if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

    # Seed tensorflow if available
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except ImportError:
        pass

    # Seed pytorch lightning if available
    try:
        import pytorch_lightning as pl
        pl.seed_everything(seed)
    except ImportError:
        pass

def get_config_summary() -> dict:
    """Return a summary of all configuration values.

    Useful for logging and debugging to ensure consistent configuration.

    Returns:
        Dictionary containing all configuration constants.
    """
    return {
        "SEED": SEED,
        "P_VALUE_THRESHOLD": P_VALUE_THRESHOLD,
        "EFFECT_SIZE_THRESHOLD": EFFECT_SIZE_THRESHOLD,
        "SAMPLE_SIZE_MINIMUM": SAMPLE_SIZE_MINIMUM,
        "MIN_SUBGROUP_SIZE": MIN_SUBGROUP_SIZE,
        "MAX_DOMAIN_PROPORTION": MAX_DOMAIN_PROPORTION,
        "MAX_CPU_VCPUS": MAX_CPU_VCPUS,
        "MAX_RAM_GB": MAX_RAM_GB,
        "MAX_RUNTIME_HOURS": MAX_RUNTIME_HOURS,
        "MONTE_CARLO_REPLICATES": MONTE_CARLO_REPLICATES,
        "MONTE_CARLO_TOLERANCE": MONTE_CARLO_TOLERANCE,
    }
