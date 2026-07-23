import os
import random
from pathlib import Path
from typing import Optional

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Random seed for reproducibility (Constitution Principle I)
RANDOM_SEED = 42

def set_seeds(seed: int = RANDOM_SEED):
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # If numpy is available, set its seed too
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def get_env_var(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable.
    
    Args:
        var_name: Name of the environment variable.
        default: Default value if not found.
        
    Returns:
        The value of the environment variable or default.
    """
    return os.getenv(var_name, default)

def ensure_dirs(*dirs: Path):
    """
    Ensure that the given directories exist.
    
    Args:
        dirs: Paths to directories to create.
    """
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
