"""
K-Fold Cross-Validation Utilities with Stratification.

Supports stratified splitting based on density and topological features.
Ensures that training and validation sets maintain consistent distributions
of inclusion density and topology type, which is critical for unbiased
generalization estimates in material stiffness prediction.
"""

import numpy as np
from typing import List, Tuple, Generator, Optional, Dict
from sklearn.model_selection import StratifiedKFold
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_dataset_metadata(metadata_path: Path) -> List[Dict]:
    """
    Load dataset metadata from JSON file.

    Args:
        metadata_path: Path to the metadata JSON file (e.g., data/processed/derivation_log.json or a combined metadata file).

    Returns:
        List of metadata dictionaries, each representing a sample.

    Raises:
        FileNotFoundError: If the metadata file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        data = json.load(f)
    
    # Handle case where data might be a single dict or a list
    if isinstance(data, dict):
        # If it's a log with a 'samples' key, use that
        if 'samples' in data:
            return data['samples']
        # Otherwise, assume the dict itself is a single sample (unlikely for dataset)
        return [data]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected metadata format: {type(data)}")

def create_stratification_bins(
    values: np.ndarray, 
    n_bins: int = 5
) -> np.ndarray:
    """
    Create stratification bins from continuous values.

    This function discretizes continuous variables (like inclusion density)
    into a fixed number of bins to enable stratified sampling.

    Args:
        values: Array of continuous values to bin.
        n_bins: Number of bins to create.

    Returns:
        Array of bin indices (integers) corresponding to each value.
    
    Raises:
        ValueError: If n_bins is less than 1 or if values array is empty.
    """
    if n_bins < 1:
        raise ValueError("n_bins must be at least 1")
    if len(values) == 0:
        return np.array([], dtype=int)
    
    # Ensure values is a numpy array
    values = np.asarray(values)
    
    # Calculate bin edges, ensuring we cover the full range
    min_val, max_val = values.min(), values.max()
    
    # Handle case where all values are the same
    if min_val == max_val:
        return np.zeros(len(values), dtype=int)
    
    # Create bin edges
    edges = np.linspace(min_val, max_val, n_bins + 1)
    
    # Digitize returns bin indices (1-based), convert to 0-based
    bins = np.digitize(values, edges[1:-1])
    
    # Ensure all values fall within valid bin range [0, n_bins-1]
    bins = np.clip(bins, 0, n_bins - 1)
    
    return bins

def create_combined_stratification(
    densities: np.ndarray,
    topologies: np.ndarray,
    density_bins: int = 3,
    topology_bins: int = 3
) -> np.ndarray:
    """
    Create combined stratification labels from multiple features.

    This function combines multiple continuous/categorical features into
    a single stratification label by creating a unique identifier for
    each combination of binned features.

    Args:
        densities: Inclusion density values (continuous).
        topologies: Topological feature values (can be continuous or categorical codes).
        density_bins: Number of bins for density.
        topology_bins: Number of bins for topology.

    Returns:
        Combined stratification labels (integers representing unique combinations).
    
    Example:
        If density_bins=3 and topology_bins=3, labels will range from 0 to 8,
        where label = density_bin * 3 + topology_bin.
    """
    if len(densities) != len(topologies):
        raise ValueError("densities and topologies must have the same length")
    
    if len(densities) == 0:
        return np.array([], dtype=int)
    
    # Convert topologies to numeric if they are categorical strings
    if topologies.dtype.kind in ['U', 'S', 'O']:
        # Create a mapping from unique values to integers
        unique_topo = np.unique(topologies)
        topo_map = {val: i for i, val in enumerate(unique_topo)}
        topo_numeric = np.array([topo_map[val] for val in topologies])
    else:
        topo_numeric = np.asarray(topologies)
    
    # Create bins for both features
    d_bins = create_stratification_bins(densities, density_bins)
    t_bins = create_stratification_bins(topo_numeric, topology_bins)
    
    # Combine into unique labels using a base that ensures no collisions
    # Using a base larger than the maximum possible topology bin count
    max_t_bins = max(topology_bins, len(np.unique(topo_numeric)))
    combined_labels = d_bins * max_t_bins + t_bins
    
    return combined_labels

def stratified_k_fold_split(
    indices: np.ndarray,
    densities: np.ndarray,
    topologies: np.ndarray,
    n_splits: int = 5,
    random_state: int = 42
) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
    """
    Generate stratified k-fold splits based on density and topology.

    This function creates train/validation splits that maintain the same
    distribution of density-topology combinations across all folds, ensuring
    that the model is evaluated on a representative sample of the data
    distribution.

    Args:
        indices: Array of sample indices to split.
        densities: Inclusion density values for each sample.
        topologies: Topological feature values for each sample.
        n_splits: Number of folds (must be <= number of unique stratification groups).
        random_state: Random seed for reproducibility.

    Yields:
        Tuple of (train_indices, val_indices) for each fold.
    
    Raises:
        ValueError: If n_splits is invalid or if there are insufficient stratification groups.
    """
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    if len(indices) == 0:
        return
    
    indices = np.asarray(indices)
    densities = np.asarray(densities)
    topologies = np.asarray(topologies)
    
    if len(indices) != len(densities) or len(indices) != len(topologies):
        raise ValueError("indices, densities, and topologies must have the same length")
    
    # Create combined stratification labels
    labels = create_combined_stratification(densities, topologies)
    
    # Check if we have enough unique groups for the requested splits
    n_unique_groups = len(np.unique(labels))
    if n_unique_groups < n_splits:
        logger.warning(
            f"Number of unique stratification groups ({n_unique_groups}) is less than "
            f"requested splits ({n_splits}). Using {n_unique_groups} splits instead."
        )
        n_splits = n_unique_groups
    
    # Initialize StratifiedKFold
    skf = StratifiedKFold(
        n_splits=n_splits, 
        shuffle=True, 
        random_state=random_state
    )
    
    # Generate splits
    for train_idx, val_idx in skf.split(indices, labels):
        yield indices[train_idx], indices[val_idx]

def get_fold_sizes(
    n_samples: int,
    n_splits: int
) -> List[int]:
    """
    Calculate fold sizes ensuring balanced splits.

    This function computes the size of each fold when splitting n_samples
    into n_splits folds, distributing any remainder samples across the
    first few folds.

    Args:
        n_samples: Total number of samples.
        n_splits: Number of folds.

    Returns:
        List of fold sizes (integers).
    
    Example:
        n_samples=10, n_splits=3 -> [4, 3, 3]
    """
    if n_samples < n_splits:
        raise ValueError(f"n_samples ({n_samples}) must be >= n_splits ({n_splits})")
    
    base_size = n_samples // n_splits
    remainder = n_samples % n_splits
    
    sizes = [base_size] * n_splits
    for i in range(remainder):
        sizes[i] += 1
    
    return sizes

def main():
    """
    Test the k-fold utilities with synthetic data.
    
    This function demonstrates the functionality of the k-fold utilities
    by creating a small synthetic dataset and performing stratified splits.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Create synthetic test data
    n_samples = 100
    np.random.seed(42)
    
    indices = np.arange(n_samples)
    densities = np.random.uniform(0.1, 0.9, n_samples)
    topologies = np.random.choice(['random', 'clustered', 'aligned'], n_samples)
    
    print(f"Testing with {n_samples} samples")
    print(f"Density range: {densities.min():.3f} to {densities.max():.3f}")
    print(f"Topology distribution: {dict(zip(*np.unique(topologies, return_counts=True)))}")
    
    # Test stratified k-fold split
    n_splits = 5
    print(f"\nPerforming {n_splits}-fold stratified split...")
    
    fold_sizes = get_fold_sizes(n_samples, n_splits)
    print(f"Expected fold sizes: {fold_sizes}")
    
    fold_num = 0
    for train_idx, val_idx in stratified_k_fold_split(
        indices, densities, topologies, n_splits=n_splits
    ):
        print(f"\nFold {fold_num + 1}:")
        print(f"  Train size: {len(train_idx)}, Val size: {len(val_idx)}")
        
        # Verify stratification
        train_dens = densities[train_idx]
        val_dens = densities[val_idx]
        train_topo = topologies[train_idx]
        val_topo = topologies[val_idx]
        
        print(f"  Train density mean: {train_dens.mean():.3f}, Val density mean: {val_dens.mean():.3f}")
        print(f"  Train topology dist: {dict(zip(*np.unique(train_topo, return_counts=True)))}")
        print(f"  Val topology dist: {dict(zip(*np.unique(val_topo, return_counts=True)))}")
        
        fold_num += 1
    
    print(f"\nCompleted {fold_num} folds successfully.")
    print("K-Fold Utilities loaded and tested successfully.")

if __name__ == "__main__":
    main()