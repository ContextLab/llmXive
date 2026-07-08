"""
Preprocessing module for genomic data analysis.

This module handles:
1. Filtering of zero-count genes from RNA-seq count matrices.
2. Handling of missing batch metadata by defaulting to random stratification.
"""
import os
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

from src.config import ensure_directories, PROJECT_ROOT
from src.versioning import compute_sha256, update_artifact_state


# Constants
MIN_SAMPLES_FOR_STRATIFICATION = 2
RANDOM_SEED = 42


def filter_zero_count_genes(
    count_matrix: pd.DataFrame,
    min_counts: int = 1,
    min_samples: int = 1
) -> pd.DataFrame:
    """
    Filter out genes that have zero counts across all samples or below a threshold.

    Args:
        count_matrix: DataFrame with genes as rows and samples as columns.
        min_counts: Minimum count sum required for a gene to be kept.
        min_samples: Minimum number of samples with non-zero counts required.

    Returns:
        Filtered DataFrame containing only genes meeting the criteria.
    """
    if count_matrix.empty:
        return count_matrix

    # Ensure numeric data
    numeric_matrix = count_matrix.apply(pd.to_numeric, errors='coerce').fillna(0)

    # Calculate total counts per gene
    total_counts = numeric_matrix.sum(axis=1)

    # Calculate number of samples with non-zero counts per gene
    non_zero_counts = (numeric_matrix > 0).sum(axis=1)

    # Filter genes
    mask = (total_counts >= min_counts) & (non_zero_counts >= min_samples)
    filtered_matrix = numeric_matrix[mask]

    return filtered_matrix


def stratify_samples(
    sample_metadata: pd.DataFrame,
    batch_column: str,
    n_subsets: int = 5,
    random_state: Optional[int] = None
) -> Dict[str, List[str]]:
    """
    Stratify samples into subsets based on batch metadata.
    If batch metadata is missing or invalid, falls back to random stratification.

    Args:
        sample_metadata: DataFrame with sample IDs as index or a column.
        batch_column: Name of the column containing batch information.
        n_subsets: Number of subsets to create.
        random_state: Random seed for reproducibility.

    Returns:
        Dictionary mapping subset names to lists of sample IDs.
    """
    if random_state is not None:
        random.seed(random_state)
        np.random.seed(random_state)

    # Handle case where sample_metadata is empty
    if sample_metadata.empty:
        return {f"subset_{i}": [] for i in range(n_subsets)}

    # Ensure sample IDs are accessible
    if batch_column not in sample_metadata.columns:
        # Fallback: random stratification
        samples = list(sample_metadata.index) if isinstance(sample_metadata.index, pd.Index) else list(sample_metadata[batch_column])
        if not samples:
            # Try to get samples from index if column doesn't exist
            if isinstance(sample_metadata.index, pd.RangeIndex):
                # If it's a default index, we can't stratify
                return {f"subset_{i}": [] for i in range(n_subsets)}
            samples = list(sample_metadata.index)

        if len(samples) < n_subsets:
            # Not enough samples for stratification
            return {f"subset_{i}": [samples[i]] if i < len(samples) else [] for i in range(n_subsets)}

        # Random shuffle and split
        shuffled_samples = samples.copy()
        random.shuffle(shuffled_samples)
        subsets = {}
        for i in range(n_subsets):
            start_idx = i * len(shuffled_samples) // n_subsets
            end_idx = (i + 1) * len(shuffled_samples) // n_subsets
            subsets[f"subset_{i}"] = shuffled_samples[start_idx:end_idx]
        return subsets

    # Check if batch column has valid data
    batch_data = sample_metadata[batch_column].dropna()
    if batch_data.empty or len(batch_data.unique()) < 2:
        # Fallback: random stratification
        samples = list(sample_metadata.index)
        if not samples:
            return {f"subset_{i}": [] for i in range(n_subsets)}

        if len(samples) < n_subsets:
            return {f"subset_{i}": [samples[i]] if i < len(samples) else [] for i in range(n_subsets)}

        shuffled_samples = samples.copy()
        random.shuffle(shuffled_samples)
        subsets = {}
        for i in range(n_subsets):
            start_idx = i * len(shuffled_samples) // n_subsets
            end_idx = (i + 1) * len(shuffled_samples) // n_subsets
            subsets[f"subset_{i}"] = shuffled_samples[start_idx:end_idx]
        return subsets

    # Standard stratification by batch
    unique_batches = batch_data.unique()
    if len(unique_batches) < n_subsets:
        # Not enough batches for n_subsets, fallback to random
        samples = list(sample_metadata.index)
        if not samples:
            return {f"subset_{i}": [] for i in range(n_subsets)}

        if len(samples) < n_subsets:
            return {f"subset_{i}": [samples[i]] if i < len(samples) else [] for i in range(n_subsets)}

        shuffled_samples = samples.copy()
        random.shuffle(shuffled_samples)
        subsets = {}
        for i in range(n_subsets):
            start_idx = i * len(shuffled_samples) // n_subsets
            end_idx = (i + 1) * len(shuffled_samples) // n_subsets
            subsets[f"subset_{i}"] = shuffled_samples[start_idx:end_idx]
        return subsets

    # Stratified sampling: ensure each subset has proportional representation
    # Group samples by batch
    batch_groups = sample_metadata.groupby(batch_column).groups
    all_samples = list(sample_metadata.index)

    # Initialize subsets
    subsets = {f"subset_{i}": [] for i in range(n_subsets)}

    # Distribute samples from each batch proportionally
    for batch, samples in batch_groups.items():
        batch_samples = list(samples)
        if len(batch_samples) < n_subsets:
            # If batch has fewer samples than subsets, add to first few subsets
            for i, sample in enumerate(batch_samples):
                subsets[f"subset_{i}"].append(sample)
        else:
            # Distribute evenly
            batch_samples_shuffled = batch_samples.copy()
            random.shuffle(batch_samples_shuffled)
            for i, sample in enumerate(batch_samples_shuffled):
                subset_idx = i % n_subsets
                subsets[f"subset_{subset_idx}"].append(sample)

    return subsets


def preprocess_dataset(
    count_matrix_path: str,
    metadata_path: Optional[str] = None,
    batch_column: Optional[str] = None,
    n_subsets: int = 5,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main preprocessing function that filters genes and creates stratified subsets.

    Args:
        count_matrix_path: Path to the count matrix file (CSV/TSV).
        metadata_path: Optional path to sample metadata file.
        batch_column: Column name for batch stratification. If None or missing, uses random.
        n_subsets: Number of subsets to create.
        output_dir: Directory to save processed files.

    Returns:
        Dictionary with paths to processed files and metadata about the preprocessing.
    """
    ensure_directories()

    # Load count matrix
    count_matrix = pd.read_csv(count_matrix_path, index_col=0)

    # Filter zero-count genes
    filtered_matrix = filter_zero_count_genes(count_matrix)

    # Prepare metadata
    sample_metadata = None
    stratification_method = "random"

    if metadata_path and os.path.exists(metadata_path):
        sample_metadata = pd.read_csv(metadata_path, index_col=0)

        # Try to use batch column if specified and available
        if batch_column and batch_column in sample_metadata.columns:
            stratification_method = "stratified"
        else:
            stratification_method = "random"
    else:
        stratification_method = "random"

    # Create subsets
    subsets = stratify_samples(
        sample_metadata if sample_metadata is not None else pd.DataFrame(index=filtered_matrix.columns),
        batch_column or "batch",
        n_subsets=n_subsets
    )

    # Set output directory
    if output_dir is None:
        output_dir = PROJECT_ROOT / "data" / "preprocessed"
    else:
        output_dir = Path(output_dir)
    ensure_directories()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save filtered matrix
    filtered_path = output_dir / "filtered_counts.csv"
    filtered_matrix.to_csv(filtered_path)

    # Save subsets
    subsets_info = {
        "subset_paths": {},
        "stratification_method": stratification_method,
        "n_subsets": n_subsets,
        "original_genes": len(count_matrix),
        "filtered_genes": len(filtered_matrix)
    }

    for subset_name, sample_ids in subsets.items():
        subset_path = output_dir / f"subset_{subset_name}.csv"
        # Filter columns to only include samples in this subset
        subset_matrix = filtered_matrix[sample_ids]
        subset_matrix.to_csv(subset_path)
        subsets_info["subset_paths"][subset_name] = str(subset_path)

    # Save metadata
    metadata_info = {
        "batch_column_used": batch_column,
        "metadata_available": metadata_path is not None and os.path.exists(metadata_path),
        "stratification_method": stratification_method
    }

    # Compute hash for versioning
    artifact_hash = compute_sha256(filtered_path)

    # Update state
    update_artifact_state(
        artifact_name="preprocessed_counts",
        path=str(filtered_path),
        hash_value=artifact_hash,
        metadata={
            "stratification_method": stratification_method,
            "n_subsets": n_subsets,
            "genes_filtered": len(count_matrix) - len(filtered_matrix)
        }
    )

    return {
        "filtered_matrix_path": str(filtered_path),
        "subsets": subsets_info,
        "metadata": metadata_info,
        "artifact_hash": artifact_hash
    }


def main():
    """
    Example usage of the preprocessing module.
    This function demonstrates how to use the preprocessing functions.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess genomic data")
    parser.add_argument("--counts", required=True, help="Path to count matrix CSV")
    parser.add_argument("--metadata", default=None, help="Path to metadata CSV")
    parser.add_argument("--batch-column", default=None, help="Column name for batch")
    parser.add_argument("--n-subsets", type=int, default=5, help="Number of subsets")
    parser.add_argument("--output-dir", default=None, help="Output directory")

    args = parser.parse_args()

    result = preprocess_dataset(
        count_matrix_path=args.counts,
        metadata_path=args.metadata,
        batch_column=args.batch_column,
        n_subsets=args.n_subsets,
        output_dir=args.output_dir
    )

    print(f"Preprocessing complete!")
    print(f"Filtered matrix saved to: {result['filtered_matrix_path']}")
    print(f"Stratification method: {result['metadata']['stratification_method']}")
    print(f"Number of genes filtered out: {result['subsets']['original_genes'] - result['subsets']['filtered_genes']}")
    print(f"Subsets created: {list(result['subsets']['subset_paths'].keys())}")


if __name__ == "__main__":
    main()
