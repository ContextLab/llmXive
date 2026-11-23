"""
Stochasticity control utilities for the llmXive project.

Ensures reproducibility by fixing random seeds across numpy, python random,
and torch (if available), and deriving unique seeds per run.
"""
import random
import os
from typing import Optional
import logging

# Try importing torch, but do not fail if it's not present (CPU-first constraint)
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

def set_seed(master_seed: int, run_id: int) -> int:
    """
    Derive a unique seed for a specific run and set it globally.

    Formula: derived_seed = master_seed + run_id

    Args:
        master_seed: The base seed for the experiment.
        run_id: The unique run identifier (0, 1, 2, ...).

    Returns:
        The derived seed value used.
    """
    derived_seed = master_seed + run_id

    # Python random
    random.seed(derived_seed)
    
    # NumPy
    try:
        import numpy as np
        np.random.seed(derived_seed)
    except ImportError:
        pass # NumPy not available, skip

    # PyTorch (if available)
    if TORCH_AVAILABLE:
        torch.manual_seed(derived_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(derived_seed)
    
    # Log the seed usage
    from utils.logging_config import log_seed_usage
    log_seed_usage(logger, derived_seed, f"Run {run_id} Initialization")

    return derived_seed

def enforce_temperature_zero():
    """
    Enforce temperature=0 for any LLM interactions (conceptual enforcement).
    In a real pipeline, this would be passed to the model API.
    Here, we log the requirement to ensure the orchestrator respects it.
    """
    logger.info("Temperature Zero Enforcement: Active. Ensure all model calls use temperature=0.")
