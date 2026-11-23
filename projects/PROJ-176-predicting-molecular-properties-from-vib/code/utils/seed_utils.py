"""
Simple deterministic‑seed helper that lazily imports torch (so the module can be imported
even on systems without CUDA support).
"""
import random
import numpy as np

def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass