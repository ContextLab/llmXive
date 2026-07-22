import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from scipy.stats import pearsonr, kstest, uniform
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for script execution
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import PROJECT_ROOT

def calculate_pearson_correlation_all_genes(
    full_log2fc: pd.Series,
    subset_log2fc: pd.Series
) -> float:
    """
    Calculate Pearson correlation of log2 fold-changes between full and subset analyses.
    Uses ALL genes to avoid Winner's Curse (per Spec Correction #1).
    
    Args:
        full_log2fc: Series of log2FC values from the full dataset analysis.
        subset_log2fc: Series of log2FC values from the subset analysis.
    
    Returns:
        Pearson correlation coefficient (r).
    """
    # Ensure alignment on gene indices
    common_genes = full_log2fc.index.intersection(subset_log2fc.index)
    if len(common_genes) == 0:
        raise ValueError("No common genes found between full and subset analyses.")
    
    x = full_log2fc.loc[common_genes].values
    y = subset_log2fc.loc[common_genes].values
    
    r, _ = pearsonr(x, y)
    return float(r)

def calculate_stability_metrics(
    correlations: List[float],
    min_threshold: float = 0.8
) -> Dict[str, float]:
    """
    Aggregate stability metrics from a list of correlation coefficients.
    
    Args:
        correlations: List of Pearson r values from subset comparisons.
        min_threshold: Minimum acceptable correlation threshold.
    
    Returns:
        Dictionary with mean, std, min, max, and pass_rate.
    """
    if not correlations:
        return {
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "pass_rate": 0.0
        }
    
    arr = np.array(correlations)
    pass_count = sum(1 for r in correlations if r >= min_threshold)
    
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "pass_rate": float(pass_count / len(correlations))
    }

def compare_parametric_empirical_pvalues(
    parametric_pvals: pd.Series,
    empirical_pvals: pd.Series,
    output_path: Optional[Union[str, Path]] = None
) -> Dict[str, float]:
    """
    Compare parametric vs empirical p-values using KS test and generate Bland-Altman plot.
    
    Args:
        parametric_pvals: Series of parametric p-values.
        empirical_pvals: Series of empirical p-values from permutation.
        output_path: Optional path to save the Bland-Altman plot.
    
    Returns:
        Dictionary with KS statistic (D) and p-value.
    """
    # Align indices
    common_idx = parametric_pvals.index.intersection(empirical_pvals.index)
    if len(common_idx) == 0:
        raise ValueError("No common indices for p-value comparison.")
    
    p_param = parametric_pvals.loc[common_idx].values
    p_emp = empirical_pvals.loc[common_idx].values
    
    # KS Test: Verify if empirical distribution matches uniform (under null)
    # Note: We test the empirical p-values against Uniform(0,1)
    ks_stat, ks_pval = kstest(p_emp, 'uniform')
    
    result = {
        "ks_statistic": float(ks_stat),
        "ks_pvalue": float(ks_pval),
        "pass_uniformity": float(ks_pval) > 0.05
    }
    
    if output_path:
        generate_bland_altman_plot(p_param, p_emp, output_path)
    
    return result

def calculate_pvalue_inflation(
    parametric_pvals: pd.Series,
    empirical_pvals: pd.Series
) -> float:
    """
    Calculate Median Absolute Deviation (MAD) between parametric and empirical p-values.
    This serves as a metric for p-value inflation/deflation.
    
    Args:
        parametric_pvals: Series of parametric p-values.
        empirical_pvals: Series of empirical p-values.
    
    Returns:
        MAD value.
    """
    common_idx = parametric_pvals.index.intersection(empirical_pvals.index)
    if len(common_idx) == 0:
        return 0.0
    
    p_param = parametric_pvals.loc[common_idx].values
    p_emp = empirical_pvals.loc[common_idx].values
    
    diff = np.abs(p_param - p_emp)
    return float(np.median(diff))

def generate_bland_altman_plot(
    p_param: np.ndarray,
    p_emp: np.ndarray,
    output_path: Union[str, Path]
) -> None:
    """
    Generate a Bland-Altman plot comparing parametric and empirical p-values.
    Since p-values are bounded [0,1], we plot the difference against the mean.
    
    Args:
        p_param: Array of parametric p-values.
        p_emp: Array of empirical p-values.
        output_path: Path to save the plot.
    """
    mean_vals = (p_param + p_emp) / 2
    diff_vals = p_param - p_emp
    
    plt.figure(figsize=(10, 8))
    plt.scatter(mean_vals, diff_vals, alpha=0.5, s=10)
    
    # Add mean difference line
    mean_diff = np.mean(diff_vals)
    plt.axhline(mean_diff, color='red', linestyle='--', label=f'Mean Diff: {mean_diff:.4f}')
    
    # Add limits of agreement (mean ± 1.96*SD)
    sd_diff = np.std(diff_vals)
    upper = mean_diff + 1.96 * sd_diff
    lower = mean_diff - 1.96 * sd_diff
    plt.axhline(upper, color='gray', linestyle=':', label=f'Upper LoA: {upper:.4f}')
    plt.axhline(lower, color='gray', linestyle=':', label=f'Lower LoA: {lower:.4f}')
    
    plt.xlabel('Mean of Parametric and Empirical P-values')
    plt.ylabel('Difference (Parametric - Empirical)')
    plt.title('Bland-Altman Plot: Parametric vs Empirical P-values')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

def apply_benjamini_hochberg_correction(
    p_values: pd.Series,
    alpha: float = 0.05
) -> Tuple[pd.Series, pd.Series]:
    """
    Apply Benjamini-Hochberg (BH) correction to a series of p-values.
    This corrects for multiple hypothesis testing to control the False Discovery Rate (FDR).
    
    Args:
        p_values: Series of raw p-values (indexed by gene ID or similar).
        alpha: Significance threshold for FDR.
    
    Returns:
        Tuple of (adjusted_p_values, boolean_rejection_mask).
        - adjusted_p_values: Series of BH-adjusted p-values (q-values).
        - boolean_rejection_mask: Boolean Series indicating which hypotheses are rejected (q < alpha).
    """
    if p_values.empty:
        return pd.Series([], dtype=float), pd.Series([], dtype=bool)
    
    # Sort p-values
    sorted_idx = p_values.argsort()
    sorted_p = p_values.iloc[sorted_idx]
    
    n = len(sorted_p)
    ranks = np.arange(1, n + 1)
    
    # Calculate BH adjusted p-values
    # q_i = (n / i) * p_i
    # Then enforce monotonicity (cumulative min from the end)
    adjusted = (n / ranks) * sorted_p.values
    
    # Enforce monotonicity: q_i <= q_{i+1}
    # Iterate from the end to the beginning
    for i in range(n - 2, -1, -1):
        if adjusted[i] > adjusted[i + 1]:
            adjusted[i] = adjusted[i + 1]
    
    # Clip to [0, 1]
    adjusted = np.clip(adjusted, 0, 1)
    
    # Restore original order
    adjusted_series = pd.Series(adjusted, index=p_values.index)
    adjusted_series = adjusted_series.iloc[sorted_idx.argsort()] # Unsort back to original order
    
    # Re-sort by original index to ensure consistency if needed, but index alignment is key
    # The above logic restores the original index order of `p_values`
    
    # Calculate rejection mask
    rejection_mask = adjusted_series < alpha
    
    return adjusted_series, rejection_mask

def main():
    """
    Main entry point for metrics module (for CLI testing if needed).
    Currently, this module is primarily imported by main.py or permutation.py.
    """
    print("metrics.py module loaded successfully.")
    print("Available functions:")
    print("  - calculate_pearson_correlation_all_genes")
    print("  - calculate_stability_metrics")
    print("  - compare_parametric_empirical_pvalues")
    print("  - calculate_pvalue_inflation")
    print("  - generate_bland_altman_plot")
    print("  - apply_benjamini_hochberg_correction")

if __name__ == "__main__":
    main()