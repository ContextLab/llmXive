import os
import random
import numpy as np
import torch

# Resource limits
MAX_CPU_CORES = int(os.getenv("MAX_CPU_CORES", "2"))
MAX_MEMORY_GB = int(os.getenv("MAX_MEMORY_GB", "7"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "3600"))

# Random seeds for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

if torch.cuda.is_available():
    torch.manual_seed(RANDOM_SEED)
    torch.cuda.manual_seed_all(RANDOM_SEED)

def set_seed(seed: int = RANDOM_SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

def validate_resource_limits() -> bool:
    """Validate that resource limits are set correctly."""
    if MAX_CPU_CORES < 1:
        raise ValueError("MAX_CPU_CORES must be at least 1")
    if MAX_MEMORY_GB < 1:
        raise ValueError("MAX_MEMORY_GB must be at least 1")
    if TIMEOUT_SECONDS < 60:
        raise ValueError("TIMEOUT_SECONDS must be at least 60")
    return True

def get_resource_limits() -> dict:
    """Get current resource limits configuration."""
    return {
        "max_cpu_cores": MAX_CPU_CORES,
        "max_memory_gb": MAX_MEMORY_GB,
        "timeout_seconds": TIMEOUT_SECONDS,
        "random_seed": RANDOM_SEED
    }
