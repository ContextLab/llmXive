import os
import random
from typing import Set, List

def set_random_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_path(relative_path: str) -> str:
    """Get absolute path relative to project root."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, relative_path)

def get_alpha_set() -> Set[float]:
    """Return the set of alpha thresholds for sensitivity analysis."""
    return {0.01, 0.05, 0.1}

def get_memory_threshold_mb() -> int:
    """Return memory threshold in MB (7 GB)."""
    return 7 * 1024  # 7 GB in MB
