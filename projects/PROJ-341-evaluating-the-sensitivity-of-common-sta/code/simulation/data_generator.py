import json
import os
from typing import Tuple, Union, Optional, List, Dict
import numpy as np
from code.simulation import get_rng

def validate_distribution_params(dist_type: str, params: Dict) -> bool:
    """
    Validate parameters for a given distribution type.
    
    Args:
        dist_type: Type of distribution ('normal', 'multinomial', etc.)
        params: Dictionary of parameters for the distribution
        
    Returns:
        bool: True if parameters are valid, False otherwise
    """
    if not isinstance(params, dict):
        return False
        
    if dist_type == 'normal':
        if 'mean' not in params or 'std' not in params:
            return False
        if not isinstance(params['mean'], (int, float)) or not isinstance(params['std'], (int, float)):
            return False
        if params['std'] <= 0:
            return False
    elif dist_type == 'multinomial':
        if 'n' not in params or 'probs' not in params:
            return False
        if not isinstance(params['n'], int) or params['n'] <= 0:
            return False
        if not isinstance(params['probs'], list):
            return False
        if len(params['probs']) == 0 or abs(sum(params['probs']) - 1.0) > 1e-6:
            return False
    elif dist_type == 'contingency':
        if 'shape' not in params:
            return False
        if not isinstance(params['shape'], tuple) or len(params['shape']) != 2:
            return False
        if params['shape'][0] <= 0 or params['shape'][1] <= 0:
            return False
    else:
        return False
        
    return True

def generate_normal_data(n: int, mean: float = 0.0, std: float = 1.0, 
                         seed: Optional[int] = None) -> np.ndarray:
    """
    Generate normally distributed data.
    
    Args:
        n: Number of samples
        mean: Mean of the distribution
        std: Standard deviation of the distribution
        seed: Optional random seed for reproducibility
        
    Returns:
        np.ndarray: Generated data
    """
    rng = get_rng(seed)
    return rng.normal(loc=mean, scale=std, size=n)

def generate_multinomial_data(n: int, probs: List[float], 
                              seed: Optional[int] = None) -> np.ndarray:
    """
    Generate multinomial distributed data.
    
    Args:
        n: Number of samples
        probs: List of probabilities for each category
        seed: Optional random seed for reproducibility
        
    Returns:
        np.ndarray: Generated data (category indices)
    """
    rng = get_rng(seed)
    return rng.choice(len(probs), size=n, p=probs)

def generate_contingency_table_data(rows: int, cols: int, 
                                    seed: Optional[int] = None) -> np.ndarray:
    """
    Generate a contingency table with specified dimensions.
    
    Args:
        rows: Number of rows
        cols: Number of columns
        seed: Optional random seed for reproducibility
        
    Returns:
        np.ndarray: Generated contingency table
    """
    rng = get_rng(seed)
    # Generate random counts with minimum 1 to avoid division by zero
    table = rng.integers(1, 20, size=(rows, cols))
    return table

def generate_two_sample_data(n1: int, n2: int, mean1: float = 0.0, 
                             mean2: float = 0.0, std: float = 1.0, 
                             seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate two samples for t-test comparison.
    
    Args:
        n1: Size of first sample
        n2: Size of second sample
        mean1: Mean of first sample
        mean2: Mean of second sample
        std: Standard deviation (assumed equal)
        seed: Optional random seed for reproducibility
        
    Returns:
        Tuple of (sample1, sample2)
    """
    rng = get_rng(seed)
    sample1 = rng.normal(loc=mean1, scale=std, size=n1)
    sample2 = rng.normal(loc=mean2, scale=std, size=n2)
    return sample1, sample2

def generate_anova_data(groups: int, n_per_group: int, 
                        means: Optional[List[float]] = None, 
                        std: float = 1.0, seed: Optional[int] = None) -> List[np.ndarray]:
    """
    Generate data for ANOVA test.
    
    Args:
        groups: Number of groups
        n_per_group: Samples per group
        means: List of means for each group (if None, uses 0 for all)
        std: Standard deviation
        seed: Optional random seed for reproducibility
        
    Returns:
        List of arrays, one per group
    """
    rng = get_rng(seed)
    if means is None:
        means = [0.0] * groups
    
    data = []
    for i in range(groups):
        group_data = rng.normal(loc=means[i], scale=std, size=n_per_group)
        data.append(group_data)
    return data
