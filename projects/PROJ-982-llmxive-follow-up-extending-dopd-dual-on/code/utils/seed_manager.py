"""
Seed manager (T021) – provides three disjoint seed ranges.

This file already existed in the repository; it is reproduced here
unchanged because the current task does not modify its behaviour.
"""
from typing import List

def get_training_seeds() -> List[int]:
    """Return the training seed range 0‑49."""
    return list(range(0, 50))

def get_evaluation_seeds() -> List[int]:
    """Return the evaluation seed range 50‑99."""
    return list(range(50, 100))

def get_baseline_seeds() -> List[int]:
    """Return the baseline seed range 1000‑1099."""
    return list(range(1000, 1100))

# Backwards‑compatible helper used by ``code.main``.
def get_seed_range_for_purpose(purpose: str) -> List[int]:
    if purpose == "training":
        return get_training_seeds()
    if purpose == "evaluation":
        return get_evaluation_seeds()
    if purpose == "baseline":
        return get_baseline_seeds()
    raise ValueError(f"Unknown purpose: {purpose}")