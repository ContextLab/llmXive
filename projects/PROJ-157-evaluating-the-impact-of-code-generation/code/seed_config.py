"""
seed_config.py
---------------
Central configuration for random seeds to ensure reproducibility across
the entire pipeline.
"""
import random
import numpy as np
from llmxive_toolkit import get_logger

log = get_logger(__name__)

# Fixed seed used for all deterministic operations
PROJECT_SEED = 20231027

def pin_seeds():
    """
    Pins random seeds for standard Python and NumPy libraries.
    """
    random.seed(PROJECT_SEED)
    np.random.seed(PROJECT_SEED)
    log.info("Pinned random seeds to %d", PROJECT_SEED)
