import os
import random
from typing import Optional

# Module‑level variable that stores the most recent seed value.
_global_seed: Optional[int] = None


def set_global_seed(seed: int) -> None:
    """
    Sets the random seed for the Python ``random`` module and the process
    environment, and records the value so that logger can later retrieve it.
    """
    global _global_seed
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    _global_seed = seed


def get_global_seed() -> Optional[int]:
    """
    Returns the seed that was most recently set via ``set_global_seed``.
    If ``set_global_seed`` has not been called, ``None`` is returned.
    """
    return _global_seed
