"""
K-Fold Cross-Validation Utilities for Stratified Sampling.

This module provides utilities for performing stratified k-fold cross-validation
on the microstructure dataset. The stratification is based on both inclusion
density and topological features (clustering coefficient) to ensure balanced
distribution across folds.

Dependencies:
  - numpy
  - scikit-learn (KFold, StratifiedKFold)
"""
import numpy as np
from typing import List, Tuple, Generator, Optional, Dict
from sklearn.model_selection import StratifiedKFold
import json
from pathlib import Path


def load_dataset_metadata(metadata_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load dataset metadata to extract stratification features.

    Args:
        metadata_path: Path to the JSON metadata file containing
                       'inclusion_density' and 'clustering_coefficient'.

    Returns:
        Tuple of (densities, clustering_coeffs) as numpy arrays.
    """
    with open(metadata_path, 'r') as f:
        data = json.load(f)

    densities = np.array([item['inclusion_density'] for item in data])
    # If clustering coefficient is missing, use density as proxy
    if 'clustering_coefficient' in data[0]:
        clustering_coeffs = np.array([item['clustering_coefficient'] for item in data])
    else:
        clustering_coeffs = densities

    return densities, clustering_coeffs


def create_stratification_bins(
    values: np.ndarray,
    n_bins: int = 5,
    bin_type: str = 'quantile'
) -> np.ndarray:
    """
    Create stratification bins from continuous values.

    Args:
        values: Array of continuous values (density or clustering).
        n_bins: Number of bins to create.
        bin_type: 'quantile' (equal frequency) or 'uniform' (equal width).

    Returns:
        Array of bin labels (integers) for each value.
    """
    if bin_type == 'quantile':
        # Use percentiles to ensure roughly equal number of samples per bin
        bins = np.percentile(values, np.linspace(0, 100, n_bins + 1))
        # Ensure unique bins
        bins = np.unique(bins)
        if len(bins) < 2:
            bins = np.array([values.min() - 1, values.max() + 1])
        bin_labels = np.digitize(values, bins[:-1])
    else:
        # Uniform binning
        min_val, max_val = values.min(), values.max()
        bins = np.linspace(min_val, max_val, n_bins + 1)
        bin_labels = np.digitize(values, bins[:-1])

    return bin_labels


def create_combined_stratification(
    densities: np.ndarray,
    clustering_coeffs: np.ndarray,
    n_density_bins: int = 5,
    n_clustering_bins: int = 5
) -> np.ndarray:
    """
    Create combined stratification labels based on density and clustering.

    This creates a multi-dimensional stratification by combining binned
    density and clustering coefficient values into a single label.

    Args:
        densities: Array of inclusion densities.
        clustering_coeffs: Array of clustering coefficients.
        n_density_bins: Number of bins for density.
        n_clustering_bins: Number of bins for clustering coefficient.

    Returns:
        Array of combined stratification labels.
    """
    density_bins = create_stratification_bins(densities, n_density_bins)
    clustering_bins = create_stratification_bins(clustering_coeffs, n_clustering_bins)

    # Combine into a single label by treating (density_bin, clustering_bin) as a tuple
    # Encode as: density_bin * n_clustering_bins + clustering_bin
    combined_labels = (density_bins - 1) * n_clustering_bins + clustering_bins

    return combined_labels


def stratified_k_fold_split(
    metadata_path: str,
    n_splits: int = 5,
    n_density_bins: int = 5,
    n_clustering_bins: int = 5,
    shuffle: bool = True,
    random_state: Optional[int] = None
) -> Generator[Tuple[List[int], List[int]], None, None]:
    """
    Generate stratified k-fold splits for the dataset.

    Stratification is performed on a combination of inclusion density
    and clustering coefficient to ensure each fold has a representative
    distribution of both features.

    Args:
        metadata_path: Path to the dataset metadata JSON file.
        n_splits: Number of folds.
        n_density_bins: Number of bins for density stratification.
        n_clustering_bins: Number of bins for clustering coefficient stratification.
        shuffle: Whether to shuffle the data before splitting.
        random_state: Random seed for reproducibility.

    Yields:
        Tuples of (train_indices, test_indices) for each fold.
    """
    # Load metadata
    densities, clustering_coeffs = load_dataset_metadata(metadata_path)
    n_samples = len(densities)

    # Create combined stratification labels
    strat_labels = create_combined_stratification(
        densities, clustering_coeffs,
        n_density_bins, n_clustering_bins
    )

    # Use StratifiedKFold from scikit-learn
    skf = StratifiedKFold(
        n_splits=n_splits,
        shuffle=shuffle,
        random_state=random_state
    )

    for train_idx, test_idx in skf.split(np.zeros(n_samples), strat_labels):
        yield train_idx.tolist(), test_idx.tolist()


def get_fold_sizes(
    metadata_path: str,
    n_splits: int = 5,
    n_density_bins: int = 5,
    n_clustering_bins: int = 5,
    random_state: Optional[int] = None
) -> List[Dict[str, int]]:
    """
    Calculate the size of each fold for reporting purposes.

    Args:
        metadata_path: Path to the dataset metadata JSON file.
        n_splits: Number of folds.
        n_density_bins: Number of bins for density stratification.
        n_clustering_bins: Number of bins for clustering coefficient stratification.
        random_state: Random seed for reproducibility.

    Returns:
        List of dictionaries containing fold statistics.
    """
    folds_info = []
    densities, clustering_coeffs = load_dataset_metadata(metadata_path)
    strat_labels = create_combined_stratification(
        densities, clustering_coeffs,
        n_density_bins, n_clustering_bins
    )

    skf = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state
    )

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(np.zeros(len(densities)), strat_labels)):
        folds_info.append({
            'fold': fold_idx + 1,
            'train_size': len(train_idx),
            'test_size': len(test_idx),
            'train_mean_density': float(np.mean(densities[train_idx])),
            'test_mean_density': float(np.mean(densities[test_idx])),
            'train_mean_clustering': float(np.mean(clustering_coeffs[train_idx])),
            'test_mean_clustering': float(np.mean(clustering_coeffs[test_idx]))
        })

    return folds_info


def main():
    """
    Main function to demonstrate k-fold split functionality.
    """
    import argparse

    parser = argparse.ArgumentParser(description='K-Fold Cross-Validation Utilities')
    parser.add_argument('--metadata', type=str, default='data/processed/derivation_log.json',
                        help='Path to dataset metadata JSON file')
    parser.add_argument('--n-splits', type=int, default=5, help='Number of folds')
    parser.add_argument('--n-density-bins', type=int, default=5, help='Number of density bins')
    parser.add_argument('--n-clustering-bins', type=int, default=5, help='Number of clustering bins')
    parser.add_argument('--report', action='store_true', help='Print fold statistics')

    args = parser.parse_args()

    # Check if metadata file exists
    if not Path(args.metadata).exists():
        print(f"Error: Metadata file not found: {args.metadata}")
        print("Please run the data generation pipeline first to create the metadata file.")
        return 1

    if args.report:
        folds_info = get_fold_sizes(
            args.metadata,
            n_splits=args.n_splits,
            n_density_bins=args.n_density_bins,
            n_clustering_bins=args.n_clustering_bins
        )

        print(f"K-Fold Split Report ({args.n_splits} folds):")
        print("-" * 60)
        for fold in folds_info:
            print(f"Fold {fold['fold']}:")
            print(f"  Train size: {fold['train_size']}, Test size: {fold['test_size']}")
            print(f"  Train mean density: {fold['train_mean_density']:.4f}")
            print(f"  Test mean density: {fold['test_mean_density']:.4f}")
            print(f"  Train mean clustering: {fold['train_mean_clustering']:.4f}")
            print(f"  Test mean clustering: {fold['test_mean_clustering']:.4f}")
            print("-" * 60)
    else:
        # Demonstrate iteration
        print(f"Iterating through {args.n_splits} stratified folds...")
        for i, (train_idx, test_idx) in enumerate(stratified_k_fold_split(
            args.metadata,
            n_splits=args.n_splits,
            n_density_bins=args.n_density_bins,
            n_clustering_bins=args.n_clustering_bins
        )):
            print(f"Fold {i+1}: Train={len(train_idx)}, Test={len(test_idx)}")

    return 0


if __name__ == '__main__':
    exit(main())
