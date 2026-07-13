from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Optional

def create_reproducible_subset(df: pd.DataFrame, size: int = 10000, seed: int = 42) -> pd.DataFrame:
    """
    Create a reproducible random subset of the dataframe.
    """
    if len(df) <= size:
        return df.reset_index(drop=True)
    
    # Use numpy random for reproducibility
    np.random.seed(seed)
    indices = np.random.choice(len(df), size=size, replace=False)
    subset = df.iloc[indices].reset_index(drop=True)
    return subset
