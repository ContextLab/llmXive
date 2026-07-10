import logging
from pathlib import Path
from typing import List, Set, Dict, Any, Union
import numpy as np
import pandas as pd
from utils.logging import get_module_logger

logger = get_module_logger(__name__)


def calculate_jaccard_index(set_a: Set, set_b: Set) -> float:
    """Calculate Jaccard index between two sets."""
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    if union == 0:
        return 0.0
    return intersection / union


def calculate_jaccard_stability_matrix(feature_sets: List[Set]) -> pd.DataFrame:
    """Calculate pairwise Jaccard index matrix for a list of feature sets."""
    n = len(feature_sets)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            matrix[i, j] = calculate_jaccard_index(feature_sets[i], feature_sets[j])
    return pd.DataFrame(matrix)


def calculate_mean_jaccard_stability(feature_sets: List[Set]) -> float:
    """Calculate mean Jaccard stability across all pairs."""
    if len(feature_sets) < 2:
        return 1.0
    matrix = calculate_jaccard_stability_matrix(feature_sets)
    # Take upper triangle excluding diagonal
    upper_tri = matrix[np.triu_indices_from(matrix, k=1)]
    return float(np.mean(upper_tri))


def benjamini_hochberg_correction(
    p_values: Union[List[float], pd.Series],
    feature_names: Union[List[str], None] = None
) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.

    Parameters
    ----------
    p_values : list[float] or pd.Series
        List of raw p-values from statistical tests.
    feature_names : list[str] or None
        Optional list of feature names corresponding to p-values.
        If None, indices are used as names.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: 'feature', 'p_value', 'p_adjusted', 'is_significant'
        Sorted by raw p-value.

    Notes
    -----
    Implements the standard Benjamini-Hochberg procedure for controlling
    the False Discovery Rate (FDR). Adjusted p-values are monotonic.
    """
    if not p_values:
        logger.warning("Empty p-values provided to BH correction.")
        return pd.DataFrame(columns=['feature', 'p_value', 'p_adjusted', 'is_significant'])

    # Convert to numpy array for processing
    p_vals = np.array(p_values)
    n = len(p_vals)

    if np.any(p_vals < 0) or np.any(p_vals > 1):
        raise ValueError("P-values must be between 0 and 1.")

    # Create a DataFrame to hold results
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n)]

    df = pd.DataFrame({
        'feature': feature_names,
        'p_value': p_vals
    })

    # Sort by p-value
    df = df.sort_values('p_value').reset_index(drop=True)

    # Calculate BH adjusted p-values
    # p_adj(i) = p(i) * n / i
    # Ensure monotonicity: p_adj(i) = min(p_adj(i), p_adj(i+1), ..., p_adj(n))
    ranks = np.arange(1, n + 1)
    df['p_adjusted'] = df['p_value'] * n / ranks

    # Enforce monotonicity (cumulative min from the end)
    # We iterate backwards to ensure p_adj[i] <= p_adj[i+1]
    df['p_adjusted'] = df['p_adjusted'].clip(upper=1.0)
    for i in range(n - 2, -1, -1):
        if df.loc[i, 'p_adjusted'] > df.loc[i + 1, 'p_adjusted']:
            df.loc[i, 'p_adjusted'] = df.loc[i + 1, 'p_adjusted']

    # Determine significance at FDR 0.05
    df['is_significant'] = df['p_adjusted'] <= 0.05

    logger.info(f"Applied Benjamini-Hochberg correction to {n} p-values. "
                f"Significant features at FDR 0.05: {df['is_significant'].sum()}")

    return df


def save_jaccard_stability_report(
    feature_sets: List[Set],
    output_path: Union[str, Path],
    metadata: Dict[str, Any] = None
) -> Path:
    """Save Jaccard stability analysis to a CSV file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mean_stability = calculate_mean_jaccard_stability(feature_sets)
    matrix_df = calculate_jaccard_stability_matrix(feature_sets)

    report = {
        'mean_stability': mean_stability,
        'num_comparisons': len(feature_sets),
        'metadata': metadata or {}
    }

    # Save matrix
    matrix_df.to_csv(output_path, index=False)

    logger.info(f"Saved Jaccard stability report to {output_path}")

    return output_path