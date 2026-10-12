"""
Package initialization for the atmospheric pressure‑earthquake project.
Sets deterministic random seeds for reproducibility.
"""
import random
import numpy as np
from llmxive_toolkit import get_logger

# Set deterministic seeds
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Initialise a module‑level logger
log = get_logger(__name__)