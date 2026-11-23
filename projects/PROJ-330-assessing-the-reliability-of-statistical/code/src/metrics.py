"""
Metrics module for calculating stability, p-value comparisons, and reporting.
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from scipy.stats import pearsonr, kstest, uniform
import logging

from src.config import PROJECT_ROOT

logger = logging.getLogger(__name__)


def calculate_pearson_correlation_all_genes(
    full_log2fc: Union[pd.Series, np.ndarray],
    subset_log2fc: Union[pd.Series, np.ndarray]
) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient and p-value between full and subset log2FC.
    
    Args:
        full_log2fc: Log2 fold changes for all genes from full dataset analysis.
        subset_log2fc: Log2 fold changes for all genes from subset analysis.
        
    Returns:
        Tuple of (correlation coefficient, p-value)
        
    Raises:
        ValueError: If inputs have different lengths or are empty.
    """
    if len(full_log2fc) != len(subset_log2fc):
        raise ValueError(f"Length mismatch: full={len(full_log2fc)}, subset={len(subset_log2fc)}")
    
    if len(full_log2fc) == 0:
        raise ValueError("Input arrays are empty")
        
    # Handle NaN values
    mask = ~(np.isnan(full_log2fc) | np.isnan(subset_log2fc))
    if np.sum(mask) < 2:
        logger.warning("Insufficient valid data points for correlation calculation")
        return 0.0, 1.0
        
    r, p = pearsonr(full_log2fc[mask], subset_log2fc[mask])
    return float(r), float(p)


def calculate_stability_metrics(
    full_results: pd.DataFrame,
    subset_results_list: List[pd.DataFrame],
    gene_column: str = "gene_id",
    log2fc_column: str = "log2FoldChange"
) -> Dict[str, float]:
    """
    Calculate stability metrics across all subsets.
    
    Args:
        full_results: DataFrame with full dataset DE results.
        subset_results_list: List of DataFrames with subset DE results.
        gene_column: Column name for gene identifiers.
        log2fc_column: Column name for log2 fold changes.
        
    Returns:
        Dictionary with stability metrics:
        - mean_correlation: Mean Pearson r across all subsets
        - min_correlation: Minimum Pearson r across all subsets
        - max_correlation: Maximum Pearson r across all subsets
        - std_correlation: Standard deviation of Pearson r across subsets
        - gene_count: Total number of genes analyzed
    """
    correlations = []
    
    # Ensure full_results is sorted by gene
    full_results = full_results.sort_values(by=gene_column).reset_index(drop=True)
    full_log2fc = full_results[log2fc_column].values
    
    for i, subset_df in enumerate(subset_results_list):
        if subset_df is None or len(subset_df) == 0:
            logger.warning(f"Subset {i} is empty, skipping")
            continue
            
        # Sort subset by gene
        subset_df = subset_df.sort_values(by=gene_column).reset_index(drop=True)
        subset_log2fc = subset_df[log2fc_column].values
        
        try:
            r, _ = calculate_pearson_correlation_all_genes(full_log2fc, subset_log2fc)
            correlations.append(r)
        except ValueError as e:
            logger.warning(f"Correlation failed for subset {i}: {e}")
            continue
    
    if len(correlations) == 0:
        logger.error("No valid correlations computed")
        return {
            "mean_correlation": 0.0,
            "min_correlation": 0.0,
            "max_correlation": 0.0,
            "std_correlation": 0.0,
            "gene_count": len(full_results),
            "n_subsets_valid": 0
        }
    
    return {
        "mean_correlation": float(np.mean(correlations)),
        "min_correlation": float(np.min(correlations)),
        "max_correlation": float(np.max(correlations)),
        "std_correlation": float(np.std(correlations)),
        "gene_count": len(full_results),
        "n_subsets_valid": len(correlations)
    }


def handle_insufficient_genes(
    gene_count: int,
    min_gene_threshold: int = 5,
    dataset_id: Optional[str] = None
) -> Dict[str, Union[bool, str, int]]:
    """
    Handle cases where the total number of genes is insufficient for analysis.
    
    This function replaces the previous 'significant genes' check with a check
    for total genes across all categories, as authorized by T016a (Spec Correction #1).
    
    Args:
        gene_count: Total number of genes found in the dataset.
        min_gene_threshold: Minimum number of genes required for analysis (default: 5).
        dataset_id: Optional identifier for the dataset being processed.
        
    Returns:
        Dictionary with:
        - is_valid: Boolean indicating if analysis can proceed
        - message: Human-readable message about the status
        - gene_count: The actual gene count
        - threshold: The minimum threshold used
        
    Raises:
        ValueError: If gene_count is negative.
    """
    if gene_count < 0:
        raise ValueError("gene_count cannot be negative")
        
    is_valid = gene_count >= min_gene_threshold
    
    if is_valid:
        message = f"Analysis can proceed with {gene_count} genes (threshold: {min_gene_threshold})"
        status = "success"
    else:
        message = (
            f"Insufficient genes for analysis: found {gene_count} genes, "
            f"minimum required is {min_gene_threshold}. "
            f"Dataset {dataset_id} will be skipped."
        )
        status = "insufficient_data"
        
    logger.info(message)
    
    return {
        "is_valid": is_valid,
        "message": message,
        "gene_count": gene_count,
        "threshold": min_gene_threshold,
        "status": status
    }


def compare_parametric_empirical_pvalues(
    parametric_pvalues: Union[pd.Series, np.ndarray],
    empirical_pvalues: Union[pd.Series, np.ndarray]
) -> Dict[str, float]:
    """
    Compare parametric and empirical p-values using KS test and calculate metrics.
    
    Args:
        parametric_pvalues: P-values from parametric test (e.g., DESeq2).
        empirical_pvalues: P-values from permutation-based empirical test.
        
    Returns:
        Dictionary with comparison metrics:
        - ks_statistic: KS test statistic
        - ks_pvalue: KS test p-value (should be > 0.05 for uniform distribution)
        - median_abs_deviation: Median absolute deviation between p-values
        - mean_abs_deviation: Mean absolute deviation between p-values
    """
    # Filter out NaN values
    valid_mask = ~(np.isnan(parametric_pvalues) | np.isnan(empirical_pvalues))
    p_param = parametric_pvalues[valid_mask]
    p_emp = empirical_pvalues[valid_mask]
    
    if len(p_param) == 0:
        logger.warning("No valid p-values for comparison")
        return {
            "ks_statistic": 0.0,
            "ks_pvalue": 0.0,
            "median_abs_deviation": 0.0,
            "mean_abs_deviation": 0.0,
            "n_compared": 0
        }
    
    # KS test against uniform distribution (for empirical p-values)
    ks_stat, ks_p = kstest(p_emp, 'uniform')
    
    # Calculate deviations
    abs_dev = np.abs(p_param - p_emp)
    median_dev = float(np.median(abs_dev))
    mean_dev = float(np.mean(abs_dev))
    
    return {
        "ks_statistic": float(ks_stat),
        "ks_pvalue": float(ks_p),
        "median_abs_deviation": median_dev,
        "mean_abs_deviation": mean_dev,
        "n_compared": len(p_param)
    }


def calculate_pvalue_inflation(
    parametric_pvalues: Union[pd.Series, np.ndarray],
    empirical_pvalues: Union[pd.Series, np.ndarray]
) -> Dict[str, float]:
    """
    Calculate p-value inflation metrics.
    
    Args:
        parametric_pvalues: P-values from parametric test.
        empirical_pvalues: P-values from empirical test.
        
    Returns:
        Dictionary with inflation metrics:
        - median_abs_deviation: Median absolute deviation (inflation measure)
        - ratio_at_0_05: Ratio of empirical to parametric p-values at 0.05 threshold
    """
    valid_mask = ~(np.isnan(parametric_pvalues) | np.isnan(empirical_pvalues))
    p_param = parametric_pvalues[valid_mask]
    p_emp = empirical_pvalues[valid_mask]
    
    if len(p_param) == 0:
        return {
            "median_abs_deviation": 0.0,
            "ratio_at_0_05": 0.0
        }
    
    abs_dev = np.abs(p_param - p_emp)
    median_dev = float(np.median(abs_dev))
    
    # Calculate ratio at 0.05 threshold
    mask_005 = p_param <= 0.05
    if np.sum(mask_005) > 0:
        ratio = float(np.mean(p_emp[mask_005] / np.maximum(p_param[mask_005], 1e-10)))
    else:
        ratio = 0.0
        
    return {
        "median_abs_deviation": median_dev,
        "ratio_at_0_05": ratio
    }


def generate_bland_altman_plot(
    parametric_pvalues: Union[pd.Series, np.ndarray],
    empirical_pvalues: Union[pd.Series, np.ndarray],
    output_path: Union[str, Path],
    title: str = "Bland-Altman Plot: Parametric vs Empirical P-values"
) -> Path:
    """
    Generate a Bland-Altman plot comparing parametric and empirical p-values.
    
    Args:
        parametric_pvalues: P-values from parametric test.
        empirical_pvalues: P-values from empirical test.
        output_path: Path to save the plot.
        title: Plot title.
        
    Returns:
        Path to the saved plot file.
    """
    import matplotlib.pyplot as plt
    import matplotlib
    
    # Ensure non-interactive backend
    matplotlib.use('Agg')
    
    valid_mask = ~(np.isnan(parametric_pvalues) | np.isnan(empirical_pvalues))
    p_param = parametric_pvalues[valid_mask]
    p_emp = empirical_pvalues[valid_mask]
    
    if len(p_param) == 0:
        logger.warning("No valid data for Bland-Altman plot")
        # Create empty plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No valid data', transform=ax.transAxes, ha='center')
        ax.set_title(title)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return Path(output_path)
    
    # Bland-Altman: plot difference vs average
    mean_vals = (p_param + p_emp) / 2
    diff_vals = p_param - p_emp
    
    mean_diff = np.mean(diff_vals)
    std_diff = np.std(diff_vals)
    upper_limit = mean_diff + 1.96 * std_diff
    lower_limit = mean_diff - 1.96 * std_diff
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(mean_vals, diff_vals, alpha=0.5, s=10)
    ax.axhline(mean_diff, color='red', linestyle='--', label=f'Mean diff: {mean_diff:.4f}')
    ax.axhline(upper_limit, color='gray', linestyle=':', label=f'Upper limit: {upper_limit:.4f}')
    ax.axhline(lower_limit, color='gray', linestyle=':', label=f'Lower limit: {lower_limit:.4f}')
    
    ax.set_xlabel('Average of Parametric and Empirical P-values')
    ax.set_ylabel('Difference (Parametric - Empirical)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return Path(output_path)


def apply_benjamini_hochberg_correction(
    pvalues: Union[pd.Series, np.ndarray, List[float]]
) -> np.ndarray:
    """
    Apply Benjamini-Hochberg correction for multiple testing.
    
    Args:
        pvalues: Array of p-values.
        
    Returns:
        Array of adjusted p-values.
    """
    pvalues = np.array(pvalues)
    n = len(pvalues)
    
    if n == 0:
        return np.array([])
        
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(pvalues)
    sorted_pvalues = pvalues[sorted_indices]
    
    # Calculate BH adjusted p-values
    ranks = np.arange(1, n + 1)
    adjusted = sorted_pvalues * n / ranks
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])
        
    # Clip to [0, 1]
    adjusted = np.clip(adjusted, 0, 1)
    
    # Restore original order
    result = np.zeros(n)
    result[sorted_indices] = adjusted
    
    return result


def main():
    """Main function for testing metrics module."""
    # Test with sample data
    np.random.seed(42)
    n_genes = 1000
    
    full_log2fc = np.random.normal(0, 1, n_genes)
    subset_log2fc = full_log2fc + np.random.normal(0, 0.1, n_genes)
    
    r, p = calculate_pearson_correlation_all_genes(full_log2fc, subset_log2fc)
    print(f"Pearson correlation: r={r:.4f}, p={p:.4f}")
    
    # Test insufficient genes handling
    result = handle_insufficient_genes(gene_count=3, min_gene_threshold=5)
    print(f"Insufficient genes check: {result}")
    
    result_valid = handle_insufficient_genes(gene_count=100, min_gene_threshold=5)
    print(f"Valid genes check: {result_valid}")


if __name__ == "__main__":
    main()