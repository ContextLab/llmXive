import json
import datetime
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

    def generate(self, n: int, seed: int, mean_diff_embodied: float, mean_diff_static: float) -> Dict[str, np.ndarray]:
        """
        Generate synthetic dataset based on configurable parameters.
        
        Args:
            n: Total number of samples.
            seed: Random seed for reproducibility.
            mean_diff_embodied: Mean gain for the embodied group.
            mean_diff_static: Mean gain for the static group.
            
        Returns:
            Dictionary containing 'pre_test_score', 'post_test_score', and 'instruction_type'.
        """
        set_seed(seed)
        
        # Generate pre-test scores (normal distribution)
        pre_scores = np.random.normal(loc=50, scale=10, size=n)
        
        # Split into two groups
        n_embodied = n // 2
        n_static = n - n_embodied
        
        # Generate gains based on instruction type
        # Embodied group: mean_diff_embodied gain
        # Static group: mean_diff_static gain
        
        gain_embodied = np.random.normal(loc=mean_diff_embodied, scale=5, size=n_embodied)
        gain_static = np.random.normal(loc=mean_diff_static, scale=5, size=n_static)
        
        # Combine gains
        gains = np.concatenate([gain_embodied, gain_static])
        
        # Calculate post-test scores
        post_scores_embodied = pre_scores[:n_embodied] + gains[:n_embodied]
        post_scores_static = pre_scores[n_embodied:] + gains[n_embodied:]
        post_scores = np.concatenate([post_scores_embodied, post_scores_static])
        
        # Instruction types
        instruction_types = np.array(['embodied'] * n_embodied + ['static'] * n_static)
        
        # Shuffle to mix groups
        indices = np.random.permutation(n)
        
        return {
            'pre_test_score': pre_scores[indices],
            'post_test_score': post_scores[indices],
            'instruction_type': instruction_types[indices]
        }

    def generate_and_save(self, n: int, seed: int, mean_diff_embodied: float, mean_diff_static: float, output_path: str) -> None:
        """
        Generate synthetic dataset and save it to a CSV file.
        
        Args:
            n: Total number of samples.
            seed: Random seed for reproducibility.
            mean_diff_embodied: Mean gain for the embodied group.
            mean_diff_static: Mean gain for the static group.
            output_path: Path to save the CSV file.
        """
        self.logger.info(f"Generating synthetic data: n={n}, seed={seed}, "
                         f"mean_diff_embodied={mean_diff_embodied}, mean_diff_static={mean_diff_static}")
        
        data = self.generate(n, seed, mean_diff_embodied, mean_diff_static)
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Write to CSV
        import csv
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['pre_test_score', 'post_test_score', 'instruction_type'])
            for i in range(n):
                writer.writerow([
                    data['pre_test_score'][i],
                    data['post_test_score'][i],
                    data['instruction_type'][i]
                ])
        
        self.logger.info(f"Synthetic data written to {output_path}")

def generate_mapping_log(n: int, seed: int, mean_diff_embodied: float, mean_diff_static: float, output_path: str) -> None:
    """
    Generate mapping log for synthetic mode to satisfy Constitution Principle VI.
    Writes the log to the specified output path.
    This MUST be called for ALL synthetic data generation runs, even if physics 
    parameters are not explicitly provided (defaults are used in that case).
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
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Mapping log written to {output_path}")

def parse_synthetic_params(args) -> Dict[str, Any]:
    """
    Parse synthetic generation parameters from CLI args or config.
    
    Args:
        args: Parsed CLI arguments object.
        
    Returns:
        Dictionary of parameters: n, seed, mean_diff_embodied, mean_diff_static.
    """
    # Default values if not provided in args
    n = getattr(args, 'n', 1000)
    seed = getattr(args, 'seed', 42)
    mean_diff_embodied = getattr(args, 'mean_diff_embodied', 5.0)
    mean_diff_static = getattr(args, 'mean_diff_static', 2.0)
    
    return {
        'n': n,
        'seed': seed,
        'mean_diff_embodied': mean_diff_embodied,
        'mean_diff_static': mean_diff_static
    }