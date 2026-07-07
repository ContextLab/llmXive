import pandas as pd
import numpy as np
from typing import Union, List

def calculate_alpha_diversity(otu_table: pd.DataFrame, metric: Union[str, List[str]] = 'all') -> pd.DataFrame:
    """
    Calculate alpha diversity metrics for an OTU table.
    
    Parameters
    ----------
    otu_table : pd.DataFrame
        Rows are samples, columns are OTUs. Values are counts.
    metric : str or list of str
        'shannon', 'simpson', 'chao1', or 'all'.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with samples as index and requested metrics as columns.
    """
    if isinstance(metric, str):
        metric = [metric]
    
    if 'all' in metric:
        metric = ['shannon', 'simpson', 'chao1']
    
    results = {}
    
    for m in metric:
        if m == 'shannon':
            results['shannon'] = _shannon_index(otu_table)
        elif m == 'simpson':
            results['simpson'] = _simpson_index(otu_table)
        elif m == 'chao1':
            results['chao1'] = _chao1_index(otu_table)
    
    return pd.DataFrame(results, index=otu_table.index)

def _shannon_index(otu_table: pd.DataFrame) -> pd.Series:
    """Calculate Shannon diversity index."""
    # Sum counts per sample
    sums = otu_table.sum(axis=1)
    
    # Avoid division by zero for empty samples
    non_zero_mask = sums > 0
    
    shannon = pd.Series(0.0, index=otu_table.index)
    
    # Only calculate for non-empty samples
    if non_zero_mask.any():
        subset = otu_table.loc[non_zero_mask]
        sums_subset = subset.sum(axis=1)
        # Proportions
        props = subset.div(sums_subset, axis=0)
        # Shannon: -sum(p * ln(p))
        # Handle 0 * ln(0) as 0
        log_props = np.where(props > 0, np.log(props), 0)
        shannon_vals = -(props * log_props).sum(axis=1)
        shannon.loc[non_zero_mask] = shannon_vals
        
    return shannon

def _simpson_index(otu_table: pd.DataFrame) -> pd.Series:
    """Calculate Simpson diversity index (1 - D)."""
    sums = otu_table.sum(axis=1)
    non_zero_mask = sums > 0
    
    simpson = pd.Series(0.0, index=otu_table.index)
    
    if non_zero_mask.any():
        subset = otu_table.loc[non_zero_mask]
        sums_subset = subset.sum(axis=1)
        props = subset.div(sums_subset, axis=0)
        # D = sum(p^2)
        d_vals = (props ** 2).sum(axis=1)
        simpson_vals = 1.0 - d_vals
        simpson.loc[non_zero_mask] = simpson_vals
        
    return simpson

def _chao1_index(otu_table: pd.DataFrame) -> pd.Series:
    """Calculate Chao1 richness estimator."""
    # S_obs: number of observed species (OTUs with count > 0)
    s_obs = (otu_table > 0).sum(axis=1)
    
    # F1: singletons (count == 1)
    f1 = (otu_table == 1).sum(axis=1)
    
    # F2: doubletons (count == 2)
    f2 = (otu_table == 2).sum(axis=1)
    
    chao1 = s_obs.copy()
    
    # Formula: S_obs + (F1^2) / (2 * F2)
    # Only apply correction if F2 > 0
    mask = f2 > 0
    if mask.any():
        correction = (f1.loc[mask] ** 2) / (2 * f2.loc[mask])
        chao1.loc[mask] += correction
    
    # If F2 == 0 but F1 > 0, Chao1 is undefined or infinite, usually handled as S_obs + F1/2 in some implementations
    # But standard Chao1 requires F2 > 0. If F2=0, we stick to S_obs or use a fallback.
    # For this implementation, we leave it as S_obs if F2=0 to avoid division by zero.
    
    return chao1