import os
import random
import numpy as np
import torch
from typing import Optional, Dict, Any, Tuple

# Default configuration values
CONFIG = {
    'split_seed': 42,
    'train_seed': 123,
    'image_size': (128, 128),
    'batch_size': 32,
    'min_feature_size_pixels': 5,
    'target_sample_size': 500,
    'stability_threshold': 0.75
}

def set_seed(seed: int) -> None:
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_split_seed() -> int:
    """Returns the seed for data splitting."""
    return CONFIG['split_seed']

def get_training_seed() -> int:
    """Returns the seed for training."""
    return CONFIG['train_seed']

def init_random_state(seed: Optional[int] = None) -> None:
    """Initializes the random state with an optional seed."""
    if seed is None:
        seed = CONFIG['train_seed']
    set_seed(seed)

def get_config_dict() -> Dict[str, Any]:
    """Returns the full configuration dictionary."""
    return CONFIG.copy()
