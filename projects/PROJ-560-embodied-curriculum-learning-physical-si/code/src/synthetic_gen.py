import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

try:
    from .utils import set_seed
except ImportError:
    import utils
    from utils import set_seed

logger = logging.getLogger(__name__)

class SyntheticDataGenerator:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate(self, n: int, seed: int, mean_diff_embodied: float, mean_diff_static: float) -> np.ndarray:
        """
        Generate synthetic dataset.
        Returns a DataFrame-like structure (numpy array or dict).
        """
        set_seed(seed)
        
        # Generate pre-test scores (normal distribution)
        pre_scores = np.random.normal(loc=50, scale=10, size=n)
        
        # Split into two groups
        n_embodied = n // 2
        n_static = n - n_embodied
        
        # Generate post-test scores based on instruction type
        # Embodied group: mean_diff_embodied gain
        # Static group: mean_diff_static gain
        
        # Simulate gain
        gain_embodied = np.random.normal(loc=mean_diff_embodied, scale=5, size=n_embodied)
        gain_static = np.random.normal(loc=mean_diff_static, scale=5, size=n_static)
        
        # Combine
        gains = np.concatenate([gain_embodied, gain_static])
        post_scores = pre_scores[:n_embodied] + gains[:n_embodied]
        post_scores_static = pre_scores[n_embodied:] + gains[n_embodied:]
        post_scores = np.concatenate([post_scores, post_scores_static])
        
        # Instruction types
        instruction_types = np.array(['embodied'] * n_embodied + ['static'] * n_static)
        
        # Shuffle to mix groups
        indices = np.random.permutation(n)
        
        return {
            'pre_test_score': pre_scores[indices],
            'post_test_score': post_scores[indices],
            'instruction_type': instruction_types[indices]
        }

def generate_mapping_log(n: int, seed: int, mean_diff_embodied: float, mean_diff_static: float) -> Dict[str, Any]:
    """
    Generate mapping log for synthetic mode to satisfy Constitution Principle VI.
    """
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "mode": "synthetic",
        "parameters": {
            "n": n,
            "seed": seed,
            "mean_diff_embodied": mean_diff_embodied,
            "mean_diff_static": mean_diff_static
        },
        "derivation": {
            "physical_variable": "gain_score",
            "abstract_concept": "learning_retention",
            "mapping_logic": "Synthetic gain scores derived from configurable mean differences to simulate embodied vs static instruction effects."
        },
        "conformance": "Constitution Principle VI (Simulation-Pedagogy Alignment) satisfied via explicit parameter mapping."
    }
    return log_entry
