import json
import os
from typing import Tuple, Union, Optional, List, Dict
import numpy as np
from code.simulation import get_rng

def validate_distribution_params(dist_type: str, params: dict) -> bool:
    """
    Validate parameters for a given distribution type.
    
    Args:
        dist_type: Type of distribution ('normal', 'multinomial', 'contingency')
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
        if 'probs' not in params:
            return False
        if not isinstance(params['probs'], (list, np.ndarray)):
            return False
        if len(params['probs']) < 2:
            return False
        if abs(sum(params['probs']) - 1.0) > 1e-6:
            return False
            
    elif dist_type == 'contingency':
        if 'rows' not in params or 'cols' not in params:
            return False
        if not isinstance(params['rows'], int) or not isinstance(params['cols'], int):
            return False
        if params['rows'] < 2 or params['cols'] < 2:
            return False
            
    return True

def generate_normal_data(n: int, mean_control: float = 0.0, mean_treatment: float = 0.5, 
                         std: float = 1.0, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate two samples from normal distributions for t-test simulation.
    
    Args:
        n: Sample size per group
        mean_control: Mean of control group
        mean_treatment: Mean of treatment group
        std: Standard deviation for both groups
        seed: Optional random seed for reproducibility
        
    Returns:
        Tuple of (control_data, treatment_data)
    """
    rng = get_rng(seed)
    control_data = rng.normal(mean_control, std, n)
    treatment_data = rng.normal(mean_treatment, std, n)
    return control_data, treatment_data

def generate_multinomial_data(n: int, probs: List[float], seed: Optional[int] = None) -> np.ndarray:
    """
    Generate multinomial data for chi-squared test simulation.
    
    Args:
        n: Total sample size
        probs: List of probabilities for each category
        seed: Optional random seed for reproducibility
        
    Returns:
        Array of category counts
    """
    rng = get_rng(seed)
    counts = rng.multinomial(n, probs)
    return counts

def generate_contingency_table_data(n: int, rows: int, cols: int, 
                                   effect_size: float = 0.0, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate a contingency table for chi-squared test simulation.
    
    Args:
        n: Total sample size
        rows: Number of rows
        cols: Number of columns
        effect_size: Effect size to introduce deviation from independence
        seed: Optional random seed for reproducibility
        
    Returns:
        2D array representing the contingency table
    """
    rng = get_rng(seed)
    
    # Create base probabilities assuming independence
    row_probs = np.ones(rows) / rows
    col_probs = np.ones(cols) / cols
    
    # Introduce effect size if needed
    if effect_size != 0.0:
        # Create a dependency matrix
        dep_matrix = np.ones((rows, cols))
        # Add effect to first cell and adjust others
        dep_matrix[0, 0] += effect_size
        # Normalize to maintain probabilities
        dep_matrix = dep_matrix / dep_matrix.sum()
        
        # Sample from the dependent distribution
        flat_probs = dep_matrix.flatten()
        counts = rng.multinomial(n, flat_probs)
        table = counts.reshape(rows, cols)
    else:
        # Sample from independent distribution
        flat_probs = np.outer(row_probs, col_probs).flatten()
        counts = rng.multinomial(n, flat_probs)
        table = counts.reshape(rows, cols)
        
    return table
