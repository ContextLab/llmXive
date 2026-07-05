"""
Configuration constants for the A/B Test Validity Audit Pipeline.

This module centralizes all deterministic seeds, statistical thresholds,
and resource caps to ensure reproducibility (Constitution Principle I)
and compliance with FR-009 (Resource Limits).
"""
import random
import os
import numpy as np
from typing import Optional, Dict, Any

# ==============================================================================
# DETERMINISTIC SEEDS (Constitution Principle I)
# ==============================================================================
# All random number generation in the pipeline MUST be seeded from this value.
SEED = 42

# Statistical thresholds (FR-004)
P_VALUE_THRESHOLD_ABSOLUTE = 0.05  # Absolute difference threshold
EFFECT_SIZE_THRESHOLD_RELATIVE = 0.05  # 5% relative effect size threshold
MIN_CORPUS_SIZE = 300  # Minimum N for power analysis (SC-020)

# Resource caps (FR-009)
MAX_RAM_GB = 2.0
MAX_CPU_VCORES = 2
MAX_RUNTIME_SECONDS = 21600  # 6 hours

# Monte Carlo parameters (FR-026)
MONTE_CARLO_REPLICATES = 10000
MONTE_CARLO_P_VALUE_TOLERANCE = 0.005

# ==============================================================================
# SEEDING UTILITIES
# ==============================================================================

def set_rng_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for all major RNGs used in the pipeline.
    
    This ensures reproducibility across runs (Constitution Principle I).
    If no seed is provided, defaults to the global SEED constant.
    
    Args:
        seed: Optional integer seed. Defaults to config.SEED if None.
    """
    if seed is None:
        seed = SEED
    
    # Seed Python's random module
    random.seed(seed)
    
    # Seed NumPy's RNG
    np.random.seed(seed)
    
    # Log the action if logging is available (optional, non-fatal if missing)
    try:
        from code.src.utils.logger import get_default_logger
        logger = get_default_logger()
        logger.info(f"RNG seeds initialized globally with value: {seed}")
    except ImportError:
        # Fallback if logger isn't initialized yet during early import
        pass

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a summary of the current configuration state.
    
    Useful for logging, manifest generation, and reproducibility checks.
    
    Returns:
        Dictionary containing key configuration parameters.
    """
    return {
        "seed": SEED,
        "p_value_threshold_absolute": P_VALUE_THRESHOLD_ABSOLUTE,
        "effect_size_threshold_relative": EFFECT_SIZE_THRESHOLD_RELATIVE,
        "min_corpus_size": MIN_CORPUS_SIZE,
        "max_ram_gb": MAX_RAM_GB,
        "max_cpu_vcores": MAX_CPU_VCORES,
        "monte_carlo_replicates": MONTE_CARLO_REPLICATES,
        "monte_carlo_tolerance": MONTE_CARLO_P_VALUE_TOLERANCE,
    }

# ==============================================================================
# IMMEDIATE EXECUTION GUARANTEE
# ==============================================================================
# Ensure seeds are set immediately upon module import to satisfy the requirement
# that "all RNGs are seeded at startup".
set_rng_seed(SEED)
