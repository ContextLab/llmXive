"""
metrics.py

Implements statistical metrics for assessing the reliability of statistical significance
in genomic datasets.

Key functionality:
- Calculate Pearson correlation of log2 fold-changes (log2FC) between full dataset
  and stratified subsets for ALL genes (per Spec Correction #1 authorized by T016a).
- Compare parametric vs. empirical p-values (KS test, Bland-Altman).
- Calculate p-value inflation metrics.
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from scipy.stats import pearsonr, kstest, uniform
import matplotlib.pyplot as plt
import seaborn as sns

from src.config import ensure_directories, PROJECT_ROOT


def calculate_pearson_correlation_all_genes(
    full_log2fc: pd.Series,
    subset_log2fc: pd.Series,
    gene_index: Optional[pd.Index] = None
) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient and p-value between full dataset
    and a subset's log2 fold-changes for ALL genes.

    Per Spec Correction #1 (T016a), this operates on ALL genes to avoid Winner's Curse.

    Args:
        full_log2fc: Series of log2FC values from the full dataset analysis.
                     Index should be gene identifiers.
        subset_log2fc: Series of log2FC values from a subset analysis.
                       Index should be gene identifiers.
        gene_index: Optional specific index to align on. If None, uses intersection.

    Returns:
        Tuple of (correlation_coefficient, p_value).
        Returns (NaN, NaN) if insufficient overlap or valid data.
    """
    # Ensure inputs are pandas Series for easy alignment
    if not isinstance(full_log2fc, pd.Series):
        full_log2fc = pd.Series(full_log2fc)
    if not isinstance(subset_log2fc, pd.Series):
        subset_log2fc = pd.Series(subset_log2fc)

    # Align on gene index (intersection)
    common_genes = full_log2fc.index.intersection(subset_log2fc.index)

    if len(common_genes) == 0:
        raise ValueError("No common genes found between full and subset analyses.")

    if len(common_genes) < 2:
        # Cannot calculate correlation with < 2 points
        return float('nan'), float('nan')

    full_vals = full_log2fc.loc[common_genes].dropna()
    subset_vals = subset_log2fc.loc[common_genes].dropna()

    # Re-intersect after dropping NaNs
    valid_idx = full_vals.index.intersection(subset_vals.index)
    if len(valid_idx) < 2:
        return float('nan'), float('nan')

    x = full_vals.loc[valid_idx].values
    y = subset_vals.loc[valid_idx].values

    # Calculate Pearson correlation
    corr, p_val = pearsonr(x, y)

    return float(corr), float(p_val)


def calculate_stability_metrics(
    full_log2fc: pd.Series,
    subset_log2fc_list: List[pd.Series]
) -> pd.DataFrame:
    """
    Calculate stability metrics (Pearson correlation) between full dataset
    and multiple subsets.

    Args:
        full_log2fc: Series of log2FC values from the full dataset.
        subset_log2fc_list: List of Series, each representing log2FC from a subset.

    Returns:
        DataFrame with columns: ['subset_id', 'correlation', 'p_value', 'n_genes'].
    """
    results = []

    for i, subset_log2fc in enumerate(subset_log2fc_list):
        corr, p_val = calculate_pearson_correlation_all_genes(full_log2fc, subset_log2fc)
        results.append({
            'subset_id': i,
            'correlation': corr,
            'p_value': p_val,
            'n_genes': len(full_log2fc.index.intersection(subset_log2fc.index).dropna())
        })

    return pd.DataFrame(results)


def compare_parametric_empirical_pvalues(
    parametric_pvals: np.ndarray,
    empirical_pvals: np.ndarray,
    method: str = 'ks'
) -> Dict[str, Union[float, bool]]:
    """
    Compare parametric p-values against empirical p-values from permutation testing.

    Per Spec Correction #2 (T024c), we use KS test to verify p-value > 0.05 (uniformity).

    Args:
        parametric_pvals: Array of parametric p-values.
        empirical_pvals: Array of empirical p-values from permutation.
        method: Method for comparison ('ks' for Kolmogorov-Smirnov).

    Returns:
        Dictionary with KS statistic, p-value, and pass/fail status.
    """
    # Filter out NaNs and zeros (log issues)
    valid_mask = ~np.isnan(parametric_pvals) & ~np.isnan(empirical_pvals)
    p_param = parametric_pvals[valid_mask]
    p_emp = empirical_pvals[valid_mask]

    if len(p_param) == 0:
        return {
            'ks_statistic': float('nan'),
            'ks_p_value': float('nan'),
            'pass_uniformity': False,
            'reason': 'No valid p-values to compare'
        }

    if method == 'ks':
        # KS test against uniform distribution [0, 1]
        # We test if empirical p-values are uniformly distributed
        ks_stat, ks_p = kstest(p_emp, 'uniform')

        # Per Spec Correction #2: pass if p-value > 0.05
        pass_uniformity = ks_p > 0.05

        return {
            'ks_statistic': float(ks_stat),
            'ks_p_value': float(ks_p),
            'pass_uniformity': pass_uniformity,
            'n_tested': len(p_emp)
        }
    else:
        raise ValueError(f"Unsupported comparison method: {method}")


def calculate_pvalue_inflation(
    parametric_pvals: np.ndarray,
    empirical_pvals: np.ndarray
) -> Dict[str, float]:
    """
    Calculate p-value inflation metrics.

    Args:
        parametric_pvals: Array of parametric p-values.
        empirical_pvals: Array of empirical p-values.

    Returns:
        Dictionary with MAD (median absolute deviation) and other inflation metrics.
    """
    valid_mask = ~np.isnan(parametric_pvals) & ~np.isnan(empirical_pvals)
    p_param = parametric_pvals[valid_mask]
    p_emp = empirical_pvals[valid_mask]

    if len(p_param) == 0:
        return {
            'mad': float('nan'),
            'median_diff': float('nan'),
            'mean_diff': float('nan')
        }

    # Log-transform p-values to handle small values better
    # Avoid log(0) by adding small epsilon
    epsilon = 1e-300
    log_p_param = -np.log10(p_param + epsilon)
    log_p_emp = -np.log10(p_emp + epsilon)

    diff = log_p_param - log_p_emp

    return {
        'mad': float(np.median(np.abs(diff - np.median(diff)))),
        'median_diff': float(np.median(diff)),
        'mean_diff': float(np.mean(diff))
    }


def generate_bland_altman_plot(
    parametric_pvals: np.ndarray,
    empirical_pvals: np.ndarray,
    output_path: Optional[Union[str, Path]] = None,
    title: str = 'Bland-Altman Plot: Parametric vs Empirical P-values'
) -> Path:
    """
    Generate a Bland-Altman plot comparing parametric and empirical p-values.

    Args:
        parametric_pvals: Array of parametric p-values.
        empirical_pvals: Array of empirical p-values.
        output_path: Path to save the plot. If None, uses default artifacts path.
        title: Plot title.

    Returns:
        Path to the saved plot file.
    """
    valid_mask = ~np.isnan(parametric_pvals) & ~np.isnan(empirical_pvals)
    p_param = parametric_pvals[valid_mask]
    p_emp = empirical_pvals[valid_mask]

    if len(p_param) == 0:
        raise ValueError("No valid p-values to plot.")

    # Log-transform for better visualization
    epsilon = 1e-300
    log_p_param = -np.log10(p_param + epsilon)
    log_p_emp = -np.log10(p_emp + epsilon)

    # Bland-Altman: mean vs difference
    mean_vals = (log_p_param + log_p_emp) / 2
    diff_vals = log_p_param - log_p_emp

    # Calculate limits of agreement
    mean_diff = np.mean(diff_vals)
    std_diff = np.std(diff_vals)
    loa_upper = mean_diff + 1.96 * std_diff
    loa_lower = mean_diff - 1.96 * std_diff

    # Create plot
    ensure_directories()
    if output_path is None:
        output_path = PROJECT_ROOT / 'artifacts' / 'bland_altman_pvalues.png'
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 8))
    sns.scatterplot(x=mean_vals, y=diff_vals, alpha=0.6, edgecolor=None)
    plt.axhline(y=mean_diff, color='red', linestyle='--', label=f'Mean Diff: {mean_diff:.3f}')
    plt.axhline(y= loa_upper, color='gray', linestyle=':', label=f'LoA Upper: { loa_upper:.3f}')
    plt.axhline(y= loa_lower, color='gray', linestyle=':', label=f'LoA Lower: { loa_lower:.3f}')

    plt.xlabel('Mean of Log10 P-values')
    plt.ylabel('Difference (Parametric - Empirical)')
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def apply_benjamini_hochberg_correction(
    p_values: np.ndarray
) -> np.ndarray:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.

    Args:
        p_values: Array of p-values.

    Returns:
        Array of adjusted p-values.
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return p_values

    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_pvals = p_values[sorted_indices]

    # Calculate adjusted p-values
    adjusted = np.empty(n)
    for i in range(n):
        rank = i + 1
        adjusted[sorted_indices[i]] = sorted_pvals[i] * n / rank

    # Ensure monotonicity (cumulative min from largest to smallest)
    for i in range(n - 2, -1, -1):
        adjusted[sorted_indices[i]] = min(adjusted[sorted_indices[i]],
                                          adjusted[sorted_indices[i + 1]])

    # Clip to [0, 1]
    adjusted = np.clip(adjusted, 0, 1)

    return adjusted


def main():
    """
    Main entry point for metrics module testing/demo.
    This function is primarily for validation and can be extended for
    integration with the main pipeline.
    """
    print("Metrics module loaded successfully.")
    print("Available functions:")
    print("  - calculate_pearson_correlation_all_genes")
    print("  - calculate_stability_metrics")
    print("  - compare_parametric_empirical_pvalues")
    print("  - calculate_pvalue_inflation")
    print("  - generate_bland_altman_plot")
    print("  - apply_benjamini_hochberg_correction")


if __name__ == "__main__":
    main()
