"""
seed_config.py
----------------
Centralized random seed configuration for the project to ensure
reproducibility across all modules.
"""
import random
import numpy as np
from llmxive_toolkit import get_logger

log = get_logger(__name__)

# Pinned project seed as per spec/plan
PROJECT_SEED = 20231027

def pin_seeds():
    """Pins random seeds for standard libraries."""
    random.seed(PROJECT_SEED)
    np.random.seed(PROJECT_SEED)
    log.info("Random seeds pinned to %d", PROJECT_SEED)
