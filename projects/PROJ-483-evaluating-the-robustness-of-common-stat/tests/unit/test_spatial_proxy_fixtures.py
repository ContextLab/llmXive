"""
Specific fixtures for Spatial Proxy generation validation.
Supports T009 requirements for mock data fixtures.
"""
import numpy as np
from typing import Dict, Any

def create_synthetic_spatial_features(
    n: int, 
    seed: int = 42
) -> Dict[str, np.ndarray]:
    """
    Creates a dictionary of features that can be used to generate
    a spatial proxy via clustering.
    
    Args:
        n: Number of samples.
        seed: Random seed.
        
    Returns:
        Dict with 'features' (n, d) and 'true_labels' (n,).
    """
    rng = np.random.default_rng(seed)
    # Create 3 distinct clusters in 2D space
    centers = np.array([[0, 0], [10, 10], [-10, 10]])
    labels = rng.integers(0, 3, size=n)
    features = np.zeros((n, 2))
    for i in range(n):
        features[i] = centers[labels[i]] + rng.normal(0, 1, 2)
    return {
        "features": features,
        "true_labels": labels
    }
