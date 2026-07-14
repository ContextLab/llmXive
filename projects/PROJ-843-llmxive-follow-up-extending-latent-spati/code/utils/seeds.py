import os
import random
import hashlib
from typing import Optional, Union
import numpy as np

def set_global_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility across libraries."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def generate_seed_from_hash(task_id: str) -> int:
    """Generate a deterministic seed from a task ID string."""
    hash_obj = hashlib.md5(task_id.encode())
    return int(hash_obj.hexdigest(), 16) % (2**32)

def set_seed_for_task(task_id: str) -> int:
    """Set a specific seed for a given task and return it."""
    seed = generate_seed_from_hash(task_id)
    set_global_seed(seed)
    return seed