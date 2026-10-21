"""Utility to set a deterministic global random seed."""

import random
import numpy as np

def set_global_seed(seed: int = 42) -> None:
    """
    Seed the common random number generators used in the project.

    Parameters
    ----------
    seed : int, optional
        The seed value to set for reproducibility, by default 42.
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
        # Silently ignore if torch is absent – the rest of the pipeline does not require it.
        pass

# Apply the default seed at import time so that any module importing this file
# gets deterministic behaviour without extra calls.
set_global_seed()
