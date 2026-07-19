"""
K-Fold Cross-Validation Utilities with Stratification.

Supports stratified splitting based on density and topological features.
"""

import numpy as np
from typing import List, Tuple, Generator, Optional, Dict
from sklearn.model_selection import StratifiedKFold
import json
from pathlib import Path

def load_dataset_metadata(metadata_path: Path) -> List[Dict]:
    """Load dataset metadata from JSON file."""
    with open(metadata_path, 'r') as f:
        return json.load(f)

def create_stratification_bins(
    values: np.ndarray, 
    n_bins: int = 5
) -> np.ndarray:
    """
    Create stratification bins from continuous values.

    Args:
        values: Array of values to bin.
        n_bins: Number of bins.

    Returns:
        Array of bin indices.
    """
    return np.digitize(values, np.linspace(values.min(), values.max(), n_bins + 1)[1:-1])

def create_combined_stratification(
    densities: np.ndarray,
    topologies: np.ndarray,
    density_bins: int = 3,
    topology_bins: int = 3
) -> np.ndarray:
    """
    Create combined stratification labels from multiple features.

    Args:
        densities: Inclusion density values.
        topologies: Topological feature values.
        density_bins: Number of bins for density.
        topology_bins: Number of bins for topology.

    Returns:
        Combined stratification labels.
    """
    d_bins = create_stratification_bins(densities, density_bins)
    t_bins = create_stratification_bins(topologies, topology_bins)
    
    # Combine into unique labels
    return d_bins * 10 + t_bins

def stratified_k_fold_split(
    indices: np.ndarray,
    densities: np.ndarray,
    topologies: np.ndarray,
    n_splits: int = 5,
    random_state: int = 42
) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
    """
    Generate stratified k-fold splits.

    Args:
        indices: Array of sample indices.
        densities: Inclusion densities.
        topologies: Topological features.
        n_splits: Number of folds.
        random_state: Random seed.

    Yields:
        Train and validation index arrays.
    """
    labels = create_combined_stratification(densities, topologies)
    
    skf = StratifiedKFold(
        n_splits=n_splits, 
        shuffle=True, 
        random_state=random_state
    )
    
    for train_idx, val_idx in skf.split(indices, labels):
        yield indices[train_idx], indices[val_idx]

def get_fold_sizes(
    n_samples: int,
    n_splits: int
) -> List[int]:
    """
    Calculate fold sizes ensuring balanced splits.

    Args:
        n_samples: Total number of samples.
        n_splits: Number of folds.

    Returns:
        List of fold sizes.
    """
    base_size = n_samples // n_splits
    remainder = n_samples % n_splits
    
    sizes = [base_size] * n_splits
    for i in range(remainder):
        sizes[i] += 1
        
    return sizes

def main():
    """Test the k-fold utilities."""
    print("K-Fold Utilities loaded successfully.")
