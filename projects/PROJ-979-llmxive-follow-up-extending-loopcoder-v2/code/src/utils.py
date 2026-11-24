"""
Utility helpers used across the llmXive pipeline.
"""
import random
import numpy as np

def set_global_seed(seed: int) -> None:
    """
    Set seeds for ``random`` and ``numpy`` (and any future libraries) to ensure
    deterministic behaviour throughout the pipeline.
    """
    random.seed(seed)
    np.random.seed(seed)