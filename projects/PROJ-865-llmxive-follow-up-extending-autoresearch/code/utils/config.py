"""
Configuration constants for the llmXive follow-up project.
"""
import os

# Statistical Power Analysis
# Reference: Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.).
# This value represents a medium effect size convention for social sciences.
EXPECTED_EFFECT_SIZE = 0.5

# Resource Limits
MAX_CPU_CORES = 2
MAX_MEMORY_GB = 7
TIMEOUT_SECONDS = 3600
BASELINE_TIMEOUT_SECONDS = 7200
BASELINE_CPU_CORES = 4
BASELINE_MEMORY_GB = 16
MAX_STREAMING_ROWS = 500
DEFAULT_SAMPLE_SIZE = 50

# Model Priority
MODEL_PRIORITY_LIST = [
    "Llama-8B-INT4", 
    "Llama-3-4B-INT4", 
    "TinyLlama-1.1B-INT4"
]

# Random Seed
SPLIT_SEED = 42

def set_seed(seed: int = SPLIT_SEED):
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    # If torch is available, set seed
    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass