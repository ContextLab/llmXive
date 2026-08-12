from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np

from .logging import get_logger
from .chemical_families import assign_chemical_family

logger = get_logger(__name__)

def get_chemical_family(element: str) -> str:
    """
    Gets the chemical family for an element.
    """
    return assign_chemical_family(element)

def sample_by_chemical_family(
    df: pd.DataFrame,
    target_rows: int,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Performs stratified sampling by chemical family.
    """
    logger.info(f"Sampling to {target_rows} rows by chemical family.")
    
    df = df.copy()
    df['chemical_family'] = df['dominant_element'].apply(assign_chemical_family)
    
    # Calculate sample size per family
    family_counts = df['chemical_family'].value_counts()
    total = len(df)
    sample_sizes = (family_counts / total * target_rows).astype(int)
    
    # Ensure we don't exceed target
    current_total = sample_sizes.sum()
    if current_total < target_rows:
        # Distribute remaining
        diff = target_rows - current_total
        sample_sizes.iloc[:diff] += 1
    
    # Sample
    sampled_df = df.groupby('chemical_family', group_keys=False).apply(
        lambda x: x.sample(n=min(sample_sizes.get(x.name, 0), len(x)), random_state=random_state)
    )
    
    sampled_df = sampled_df.drop(columns=['chemical_family'])
    logger.info(f"Sampled {len(sampled_df)} rows.")
    return sampled_df
