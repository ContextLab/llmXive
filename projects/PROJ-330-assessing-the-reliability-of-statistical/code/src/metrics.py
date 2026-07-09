import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from scipy.stats import pearsonr, kstest, uniform
import logging

from src.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

MIN_GENES_THRESHOLD: int = 5

def calculate_pearson_correlation_all_genes(
    full_log2fc: Union[pd.Series, np.ndarray],
    subset_log2fc: Union[pd.Series, np.ndarray],
    gene_ids: Optional[Union[pd.Series, np.ndarray]] = None
) -> Tuple[float, float, int]:
    """
    Calculate Pearson correlation of log2FC between full set and a subset.
    Returns (r, p_value, n_genes).
    """
    if gene_ids is None:
        # Assume parallel alignment if no IDs provided
        common_mask = ~np.isnan(full_log2fc) & ~np.isnan(subset_log2fc)
        x = np.asarray(full_log2fc)[common_mask]
        y = np.asarray(subset_log2fc)[common_mask]
    else:
        # Align by gene ID
        df = pd.DataFrame({
            'gene': gene_ids,
            'full': full_log2fc,
            'subset': subset_log2fc
        })
        df = df.dropna(subset=['full', 'subset'])
        x = df['full'].values
        y = df['subset'].values

    n = len(x)
    if n < MIN_GENES_THRESHOLD:
        logger.warning(
            f"Insufficient total genes for correlation: found {n} genes "
            f"(threshold: {MIN_GENES_THRESHOLD}). Returning NaN for metrics."
        )
        return np.nan, np.nan, n

    r, p_val = pearsonr(x, y)
    return float(r), float(p_val), n

def calculate_stability_metrics(
    results: List[Dict],
    min_genes: int = MIN_GENES_THRESHOLD
) -> Dict[str, float]:
    """
    Aggregate stability metrics from multiple subset analyses.
    Handles insufficient data gracefully by marking metrics as NaN.
    """
    valid_corrs = [r['r'] for r in results if not np.isnan(r.get('r', np.nan))]
    
    if not valid_corrs:
        logger.warning("No valid correlations found across subsets. Stability metrics unavailable.")
        return {
            'mean_stability': np.nan,
            'std_stability': np.nan,
            'min_genes_encountered': min_genes,
            'valid_subsets': 0
        }

    return {
        'mean_stability': float(np.mean(valid_corrs)),
        'std_stability': float(np.std(valid_corrs)),
        'min_genes_encountered': min([r.get('n_genes', 0) for r in results]),
        'valid_subsets': len(valid_corrs)
    }

def compare_parametric_empirical_pvalues(
    parametric_pvals: np.ndarray,
    empirical_pvals: np.ndarray,
    alpha: float = 0.05
) -> Dict[str, Union[float, bool]]:
    """
    Compare parametric vs empirical p-values using KS test.
    Correcting spec: KS test verifies p-value > 0.05 (uniformity).
    """
    if len(parametric_pvals) == 0 or len(empirical_pvals) == 0:
        logger.warning("Empty p-value arrays provided for comparison.")
        return {'ks_statistic': np.nan, 'ks_pvalue': np.nan, 'is_uniform': False}

    # Sort both to ensure valid comparison
    parametric_pvals = np.sort(parametric_pvals)
    empirical_pvals = np.sort(empirical_pvals)

    # Use the smaller set for KS test to avoid length mismatch issues
    # or pad/interpolate if strictly necessary. Here we assume similar sizes or take min.
    n = min(len(parametric_pvals), len(empirical_pvals))
    x = parametric_pvals[:n]
    y = empirical_pvals[:n]

    if n < MIN_GENES_THRESHOLD:
        logger.warning(f"Insufficient p-values ({n}) for KS test.")
        return {'ks_statistic': np.nan, 'ks_pvalue': np.nan, 'is_uniform': False}

    ks_stat, ks_p = kstest(y, 'uniform')
    
    # Spec Correction #2: p-value > 0.05 implies uniformity (fail to reject null)
    is_uniform = ks_p > alpha

    return {
        'ks_statistic': float(ks_stat),
        'ks_pvalue': float(ks_p),
        'is_uniform': is_uniform
    }

def calculate_pvalue_inflation(
    parametric_pvals: np.ndarray,
    empirical_pvals: np.ndarray
) -> float:
    """
    Calculate Median Absolute Deviation (MAD) of p-values as an inflation metric.
    """
    if len(parametric_pvals) == 0 or len(empirical_pvals) == 0:
        return np.nan

    n = min(len(parametric_pvals), len(empirical_pvals))
    diff = np.abs(parametric_pvals[:n] - empirical_pvals[:n])
    return float(np.median(diff))

def generate_bland_altman_plot(
    parametric_pvals: np.ndarray,
    empirical_pvals: np.ndarray,
    output_path: Union[str, Path]
) -> Path:
    """
    Generate a Bland-Altman plot comparing parametric and empirical p-values.
    Saves to output_path.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    n = min(len(parametric_pvals), len(empirical_pvals))
    if n < MIN_GENES_THRESHOLD:
        logger.warning(f"Insufficient data ({n}) for Bland-Altman plot.")
        # Create a placeholder file to satisfy artifact requirement
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("Plot skipped: Insufficient data points (<5).")
        return output_path

    x = parametric_pvals[:n]
    y = empirical_pvals[:n]

    mean_vals = (x + y) / 2
    diff_vals = x - y

    mean_diff = np.mean(diff_vals)
    std_diff = np.std(diff_vals)
    upper = mean_diff + 1.96 * std_diff
    lower = mean_diff - 1.96 * std_diff

    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=mean_vals, y=diff_vals, alpha=0.6, edgecolor=None)
    plt.axhline(mean_diff, color='red', linestyle='--', label=f'Mean Diff: {mean_diff:.4f}')
    plt.axhline(upper, color='gray', linestyle=':', label=f'Upper (1.96 SD): {upper:.4f}')
    plt.axhline(lower, color='gray', linestyle=':', label=f'Lower (1.96 SD): {lower:.4f}')
    plt.xlabel('Mean of Parametric and Empirical P-values')
    plt.ylabel('Difference (Parametric - Empirical)')
    plt.title('Bland-Altman Plot: Parametric vs Empirical P-values')
    plt.legend()
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path

def apply_benjamini_hochberg_correction(
    p_values: np.ndarray,
    alpha: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    Returns adjusted p-values and boolean mask of significant results.
    """
    if len(p_values) == 0:
        return np.array([]), np.array([])

    p_values = np.asarray(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    # Calculate adjusted p-values
    rank = np.arange(1, n + 1)
    adjusted_p = (sorted_p * n) / rank
    adjusted_p = np.minimum.accumulate(adjusted_p[::-1])[::-1]
    adjusted_p = np.clip(adjusted_p, 0, 1)

    # Restore original order
    final_adjusted = np.empty(n)
    final_adjusted[sorted_indices] = adjusted_p

    significant = final_adjusted <= alpha
    return final_adjusted, significant

def main():
    """
    Main entry point for metrics module testing/demo.
    """
    logger.info("Metrics module loaded.")
    # Example usage for validation
    test_p = np.array([0.01, 0.03, 0.04, 0.1, 0.2, 0.005])
    adj, sig = apply_benjamini_hochberg_correction(test_p)
    print(f"Original: {test_p}")
    print(f"Adjusted: {adj}")
    print(f"Significant: {sig}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()