import os
import random
from typing import Dict, Any, Optional
import numpy as np

def set_seed(seed: int = 42) -> None:
    """
    Sets the random seed for reproducibility across numpy, random, and torch (if available).
    
    Args:
        seed: The random seed to set.
    """
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_config() -> Dict[str, Any]:
    """
    Returns the project configuration dictionary.
    
    Returns:
        Dict: Configuration parameters including paths, seeds, and analysis parameters.
    """
    config = {
        "seed": 42,
        "window_size": 60,  # seconds. Note: This deviates from the Constitution's 30s default.
                            # Justification: See docs/technical-design.md (Task T004a).
                            # The Spec (FR-003) mandates 60s for the Schaefer 200 atlas resolution
                            # to ensure stable correlation estimation, overriding the 30s default.
        "step_size": 1,     # seconds
        "fd_threshold": 0.2, # mm
        "project_root": os.getenv("PROJECT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "data_results": "data/results",
        "figures": "figures",
        # Placeholder for subject IDs. In a real scenario, these would be loaded from a file.
        "subject_ids": ["100307", "100913", "101111"] 
    }
    return config
