"""
Environment configuration management for the Quantum Cognition project.

This module handles:
- Random seed pinning (Python, NumPy, PyTorch)
- Device selection (enforced CPU)
- Batch size configuration
- Environment variable propagation
"""
import os
import random
import torch
import numpy as np
from typing import Optional, Dict, Any

# Default configuration values
DEFAULT_SEED = 42
DEFAULT_DEVICE = "cpu"
DEFAULT_BATCH_SIZE = 8
DEFAULT_NUM_WORKERS = 0  # CPU-only, avoid multiprocessing overhead

class Config:
    """
    Central configuration holder for the experiment.
    
    Attributes:
        seed (int): Random seed for reproducibility.
        device (str): Compute device ('cpu' enforced).
        batch_size (int): Batch size for data loaders.
        num_workers (int): Number of workers for data loading.
        data_dir (str): Root directory for data.
        results_dir (str): Root directory for results.
    """
    def __init__(
        self,
        seed: int = DEFAULT_SEED,
        device: str = DEFAULT_DEVICE,
        batch_size: int = DEFAULT_BATCH_SIZE,
        num_workers: int = DEFAULT_NUM_WORKERS,
        data_dir: Optional[str] = None,
        results_dir: Optional[str] = None
    ):
        # Enforce CPU constraint (SC-004)
        if device != "cpu":
            raise ValueError(
                f"Device '{device}' is not allowed. "
                "This project runs on CPU-only CI. Use 'cpu'."
            )
        
        self.seed = seed
        self.device = device
        self.batch_size = batch_size
        self.num_workers = num_workers
        
        # Resolve paths relative to project root if not provided
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.data_dir = data_dir or os.path.join(project_root, "data")
        self.results_dir = results_dir or os.path.join(self.data_dir, "results")
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)

    def set_seed(self) -> None:
        """
        Pin all random number generators to the configured seed.
        
        This ensures reproducibility across runs.
        """
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            # Should not happen in this project, but safe to include
            torch.cuda.manual_seed_all(self.seed)
        
        # Deterministic behavior for PyTorch (may impact performance)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as a dictionary."""
        return {
            "seed": self.seed,
            "device": self.device,
            "batch_size": self.batch_size,
            "num_workers": self.num_workers,
            "data_dir": self.data_dir,
            "results_dir": self.results_dir
        }

# Global configuration instance (lazy initialization)
_global_config: Optional[Config] = None

def get_config(
    seed: Optional[int] = None,
    device: Optional[str] = None,
    batch_size: Optional[int] = None
) -> Config:
    """
    Retrieve or create the global configuration instance.
    
    Args:
        seed: Override default seed.
        device: Override default device (must be 'cpu').
        batch_size: Override default batch size.
        
    Returns:
        Config: The active configuration object.
    """
    global _global_config
    
    if _global_config is None:
        _global_config = Config(
            seed=seed if seed is not None else DEFAULT_SEED,
            device=device if device is not None else DEFAULT_DEVICE,
            batch_size=batch_size if batch_size is not None else DEFAULT_BATCH_SIZE
        )
        _global_config.set_seed()
        
    return _global_config

def set_environment(
    seed: Optional[int] = None,
    device: Optional[str] = None,
    batch_size: Optional[int] = None
) -> Config:
    """
    Convenience wrapper to set environment and return config.
    
    This function should be called at the entry point of any script
    to ensure consistent environment setup.
    
    Args:
        seed: Random seed.
        device: Device string (enforced 'cpu').
        batch_size: Batch size.
        
    Returns:
        Config: The configured environment object.
    """
    config = get_config(seed=seed, device=device, batch_size=batch_size)
    
    # Propagate to environment variables for downstream tools if needed
    os.environ["PROJECT_SEED"] = str(config.seed)
    os.environ["PROJECT_DEVICE"] = config.device
    os.environ["PROJECT_BATCH_SIZE"] = str(config.batch_size)
    
    return config