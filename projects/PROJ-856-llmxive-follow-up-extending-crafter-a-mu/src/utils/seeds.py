"""Utility to set a deterministic global random seed (seed=42 by default)."""

import random

import numpy as np

# Public constant for verification as required by the task specification.
SEED = 42

# Alias kept for backward compatibility with existing code.
GLOBAL_SEED = SEED


def set_global_seed(seed: int = SEED) -> None:
    """
    Seed the common random number generators used in the project.

    Parameters
    ----------
    seed : int, optional
        The seed value to set for reproducibility, by default SEED (42).
    """
    random.seed(seed)
    np.random.seed(seed)
    # Torch may not be installed in every environment; seed if available.
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        # Silently ignore if torch is absent – the rest of the pipeline
        # does not require it.
        pass


# Apply the default seed at import time so that any module importing this
# file gets deterministic behaviour without extra calls.
set_global_seed()
