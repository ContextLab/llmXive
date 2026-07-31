import os
from pathlib import Path
from typing import Dict, Any

def get_config() -> Dict[str, Any]:
    """
    Returns the configuration dictionary.
    MUST define keys: W_LIST, L_LIST, NUM_REALIZATIONS, SEED, 
    WEAK_DISORDER_CUTOFF, NUMERICAL_RESIDUAL_THRESHOLD, MAX_TM_ITERATIONS.
    """
    project_root = Path(__file__).parent.parent
    return {
        "PROJECT_ROOT": str(project_root),
        "W_LIST": [0.5, 1.0, 1.5, 2.0],
        "L_LIST": [100, 200, 400, 800, 1600],
        "NUM_REALIZATIONS": 10,
        "SEED": 42,
        "WEAK_DISORDER_CUTOFF": 1.0,
        "NUMERICAL_RESIDUAL_THRESHOLD": 1e-6,
        "MAX_TM_ITERATIONS": 1000
    }

class Config:
    """Optional class wrapper if needed elsewhere."""
    pass
