import numpy as np
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

def compute_sample_entropy(time_series: np.ndarray, m: int = 2, r: float = 0.2) -> float:
    """
    Compute Sample Entropy (SampEn) for a 1D time series.
    
    Args:
        time_series: 1D array of time series data.
        m: Embedding dimension (default: 2).
        r: Tolerance threshold (default: 0.2 * std).
        
    Returns:
        Sample entropy value.
    """
    if len(time_series) < m + 1:
        return np.nan
        
    # Normalize r by standard deviation if r is a fraction
    if r < 1.0:
        r = r * np.std(time_series)
        
    n = len(time_series)
    
    # Count similar templates
    def count_matches(vec, m, r):
        count = 0
        for i in range(len(vec) - m):
            for j in range(i + 1, len(vec) - m):
                # Chebyshev distance
                if np.max(np.abs(vec[i:i+m] - vec[j:j+m])) < r:
                    count += 1
        return count
        
    B = count_matches(time_series, m, r)
    A = count_matches(time_series, m + 1, r)
    
    if B == 0:
        return np.nan
        
    sampen = -np.log(A / B) if B > 0 else np.nan
    return sampen

def compute_multiscale_entropy(time_series: np.ndarray, scales: range = range(1, 21), 
                               m: int = 2, r: float = 0.2) -> np.ndarray:
    """
    Compute Multiscale Sample Entropy across multiple scales.
    
    Args:
        time_series: 1D array of time series data.
        scales: Range of scale factors to compute.
        m: Embedding dimension.
        r: Tolerance threshold.
        
    Returns:
        Array of entropy values for each scale.
    """
    entropy_values = []
    
    for scale in scales:
        # Coarse-graining
        coarse = []
        for i in range(0, len(time_series) - (scale - 1), scale):
            coarse.append(np.mean(time_series[i:i+scale]))
        
        if len(coarse) < m + 2:
            entropy_values.append(np.nan)
        else:
            ent = compute_sample_entropy(np.array(coarse), m, r)
            entropy_values.append(ent)
            
    return np.array(entropy_values)

def aggregate_networks(parcel_data: np.ndarray, network_map: dict) -> dict:
    """
    Aggregate parcel-level entropy values into network-level metrics.
    
    Args:
        parcel_data: Dictionary of parcel_id -> entropy_value.
        network_map: Dictionary of network_name -> list of parcel_ids.
        
    Returns:
        Dictionary of network_name -> mean entropy.
    """
    network_entropy = {}
    
    for network, parcels in network_map.items():
        values = [parcel_data.get(p, np.nan) for p in parcels]
        valid_values = [v for v in values if not np.isnan(v)]
        
        if valid_values:
            network_entropy[network] = np.mean(valid_values)
        else:
            network_entropy[network] = np.nan
            
    return network_entropy
