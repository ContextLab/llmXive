"""
Synthetic Fallback: Generates a small dataset if primary data is unavailable.
Used only when real data fetch fails (per T015b).
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any

def generate_fallback_dataset(steps: int = 1000) -> pd.DataFrame:
    """
    Generate a minimal fallback dataset for testing.
    This is ONLY used if real data sources are unreachable.
    """
    data = {
        "step": range(steps),
        "coherence_score": np.random.rand(steps) * 0.5 + 0.25,
        "diversity_score": np.random.rand(steps) * 0.5 + 0.25,
        "param": ["A"] * steps
    }
    return pd.DataFrame(data)
