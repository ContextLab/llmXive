"""
Very small stub of the ``numpy`` package.

Only the functionality required by the existing project scripts is provided.
The goal is to avoid adding a heavyweight external dependency while keeping
the import statements ``import numpy as np`` functional.
"""

import math
import random
from typing import Iterable, List, Sequence

# -------------------------------------------------------------------------
# Array‑like helpers
# -------------------------------------------------------------------------
def array(seq: Iterable) -> List:
    """Return a plain Python list representing a NumPy array."""
    return list(seq)

def mean(seq: Sequence[float]) -> float:
    """Arithmetic mean of a sequence."""
    if not seq:
        return 0.0
    return sum(seq) / len(seq)

def std(seq: Sequence[float]) -> float:
    """Population standard deviation."""
    if not seq:
        return 0.0
    m = mean(seq)
    return math.sqrt(sum((x - m) ** 2 for x in seq) / len(seq))

def sqrt(x: float) -> float:
    """Square‑root."""
    return math.sqrt(x)

# -------------------------------------------------------------------------
# Minimal ``np.random`` namespace
# -------------------------------------------------------------------------
class _RandomModule:
    @staticmethod
    def seed(s: int) -> None:
        random.seed(s)

    @staticmethod
    def rand() -> float:
        """Return a single float in [0, 1)."""
        return random.random()

    @staticmethod
    def randn() -> float:
        """Return a single float from a standard normal distribution."""
        return random.gauss(0.0, 1.0)

random = _RandomModule()
