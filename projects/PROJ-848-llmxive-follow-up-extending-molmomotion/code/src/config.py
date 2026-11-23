"""
Configuration management for the MolmoMotion follow-up project.

This module centralizes configuration parameters including random seeds,
device constraints, and artifact paths.
"""

import os
import random
import numpy as np

class Config:
    """Holds all project configuration."""
    
    def __init__(self):
        # Random Seeds
        self.random_seed = int(os.getenv("RANDOM_SEED", "42"))
        self.torch_seed = self.random_seed
        self.numpy_seed = self.random_seed
        
        # Device Constraints
        self.device = os.getenv("DEVICE", "cpu")
        if self.device not in ["cpu", "cuda"]:
            raise ValueError(f"Invalid device specified: {self.device}. Must be 'cpu' or 'cuda'.")
        
        # Memory Constraints
        self.target_memory_gb = float(os.getenv("TARGET_MEMORY_GB", "7.0"))
        self.min_sample_threshold = int(os.getenv("MIN_SAMPLE_THRESHOLD", "1000"))
        
        # Paths
        self.project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_raw_dir = os.path.join(self.project_root, "data", "raw")
        self.data_processed_dir = os.path.join(self.project_root, "data", "processed")
        self.data_results_dir = os.path.join(self.project_root, "data", "results")
        
        # Ensure directories exist
        os.makedirs(self.data_raw_dir, exist_ok=True)
        os.makedirs(self.data_processed_dir, exist_ok=True)
        os.makedirs(self.data_results_dir, exist_ok=True)
        
        # Output paths
        self.subsampled_instances_path = os.path.join(self.data_processed_dir, "subsampled_instances.parquet")
        self.instruction_pairs_path = os.path.join(self.data_processed_dir, "instruction_pairs.jsonl")
        self.predictions_path = os.path.join(self.data_results_dir, "predictions.jsonl")
        
        # Initialize seeds
        self._set_seeds()

    def _set_seeds(self):
        """Sets random seeds for reproducibility."""
        random.seed(self.random_seed)
        np.random.seed(self.numpy_seed)
        try:
            import torch
            torch.manual_seed(self.torch_seed)
            if self.device == "cuda":
                torch.cuda.manual_seed_all(self.torch_seed)
        except ImportError:
            pass

# Singleton instance
_config_instance = None

def get_config() -> Config:
    """Returns the singleton Config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
