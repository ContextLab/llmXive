import numpy as np
from typing import Tuple, Union, Optional, List
import json
import os
from code.simulation import get_rng

def generate_normal_data(n: int, mean: float = 0, std: float = 1, seed: Optional[int] = None) -> np.ndarray:
    """Generate normal distributed data."""
    rng = get_rng(seed)
    return rng.normal(mean, std, n)

def generate_multinomial_data(n: int, probs: List[float], seed: Optional[int] = None) -> np.ndarray:
    """Generate multinomial distributed data."""
    rng = get_rng(seed)
    return rng.multinomial(n, probs)

def generate_contingency_table_data(total_n: int, effect_size: float = 0, seed: Optional[int] = None) -> np.ndarray:
    """Generate a 2x2 contingency table."""
    rng = get_rng(seed)
    # Base probabilities
    p11 = 0.5 + effect_size * 0.1
    p12 = 0.5 - effect_size * 0.1
    p21 = 0.5 - effect_size * 0.1
    p22 = 0.5 + effect_size * 0.1
    
    # Normalize
    total_p = p11 + p12 + p21 + p22
    probs = [p11/total_p, p12/total_p, p21/total_p, p22/total_p]
    
    counts = rng.multinomial(total_n, probs)
    return np.array(counts).reshape(2, 2)

def validate_distribution_params(dist_type: str, params: Dict) -> bool:
    """Validate parameters for a distribution."""
    if dist_type == 'normal':
        return params.get('mean') is not None and params.get('std') is not None
    elif dist_type == 'multinomial':
        return 'probs' in params and sum(params['probs']) == 1.0
    return False

if __name__ == '__main__':
    print("Data Generator Module")
