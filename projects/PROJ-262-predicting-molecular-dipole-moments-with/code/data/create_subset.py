from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Optional

def create_reproducible_subset(df: pd.DataFrame, size: int = 10000, seed: int = 42) -> pd.DataFrame:
    """
    Creates a reproducible random subset of the dataframe.
    
    Args:
        df: Input DataFrame
        size: Target number of rows
        seed: Random seed for reproducibility
        
    Returns:
        Subset DataFrame
    """
    if len(df) <= size:
        return df.copy()
    
    # Set seed for reproducibility
    np.random.seed(seed)
    
    # Randomly sample indices
    indices = np.random.choice(len(df), size=size, replace=False)
    
    return df.iloc[indices].reset_index(drop=True)
