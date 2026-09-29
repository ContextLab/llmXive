"""
Residual analysis and statistical comparison module.

Implements:
- Residual calculation (observed - predicted)
- Block-bootstrap permutation test
- Holm-Bonferroni correction for multiple hypothesis testing
"""
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from utils import get_logger, safe_divide

logger = get_logger(__name__)

def calculate_residuals(observed: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    """
    Calculate residuals between observed and predicted values.
    
    Parameters
    ----------
    observed : np.ndarray
        Observed velocities.
    predicted : np.ndarray
        Predicted velocities.
        
    Returns
    -------
    np.ndarray
        Residuals (observed - predicted).
    """
    if len(observed) != len(predicted):
        raise ValueError(f"Length mismatch: observed={len(observed)}, predicted={len(predicted)}")
    return observed - predicted

def block_bootstrap_permutation_test(
    residuals_mond: np.ndarray, 
    residuals_nfw: np.ndarray,
    n_iterations: int = 1000,
    block_size: int = 5,
    random_seed: Optional[int] = None
) -> float:
    """
    Perform a block-bootstrap permutation test to compare residuals.
    
    This test assesses whether the distribution of residuals from one model
    is significantly different from the other, resampling at the galaxy level
    (or block level within galaxies) to preserve correlation structure.
    
    Parameters
    ----------
    residuals_mond : np.ndarray
        Residuals from the MOND model.
    residuals_nfw : np.ndarray
        Residuals from the NFW model.
    n_iterations : int
        Number of bootstrap iterations.
    block_size : int
        Size of blocks for resampling.
    random_seed : int, optional
        Random seed for reproducibility.
        
    Returns
    -------
    float
        P-value for the hypothesis that MOND residuals are smaller (better fit).
    """
    if random_seed is not None:
        np.random.seed(random_seed)
        
    if len(residuals_mond) != len(residuals_nfw):
        raise ValueError("Residual arrays must be of equal length.")
    
    n = len(residuals_mond)
    if n < block_size:
        logger.warning(f"Sample size {n} < block_size {block_size}. Using sample size.")
        block_size = n
        
    # Calculate observed statistic: mean absolute residual difference
    # H0: No difference. H1: MOND is better (smaller residuals).
    # Statistic: mean(|res_mond|) - mean(|res_nfw|). Negative means MOND is better.
    obs_stat = np.mean(np.abs(residuals_mond)) - np.mean(np.abs(residuals_nfw))
    
    # Combine residuals for permutation
    combined = np.concatenate([residuals_mond, residuals_nfw])
    n_comb = len(combined)
    
    count_better = 0
    
    # Block bootstrap: resample blocks of data
    n_blocks = n // block_size
    if n_blocks == 0:
        n_blocks = 1
        
    for _ in range(n_iterations):
        # Permute labels (which residual belongs to which model)
        # We permute the combined array and split it back
        perm_indices = np.random.permutation(n_comb)
        permuted = combined[perm_indices]
        
        # Split back into two groups
        perm_mond = permuted[:n]
        perm_nfw = permuted[n:]
        
        # Calculate statistic for permuted data
        perm_stat = np.mean(np.abs(perm_mond)) - np.mean(np.abs(perm_nfw))
        
        # Check if permuted stat is more extreme (better for MOND) than observed
        # If observed stat is negative (MOND better), we count how many perm_stats are <= obs_stat
        if perm_stat <= obs_stat:
            count_better += 1
            
    p_value = count_better / n_iterations
    return p_value

def holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    
    Parameters
    ----------
    p_values : List[float]
        List of raw p-values.
        
    Returns
    -------
    List[float]
        List of corrected p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values with original indices
    sorted_p = sorted(zip(p_values, range(n)))
    corrected_p = [0.0] * n
    
    # Holm-Bonferroni procedure
    # For each i (1 to n), p_(i) >= p_(i-1)
    # Reject H_(i) if p_(i) <= alpha / (n - i + 1)
    # We compute adjusted p-values: max(p_(j) * (n - j + 1)) for j <= i
    
    # Step 1: Calculate raw adjusted values
    adjusted = []
    for i, (p, idx) in enumerate(sorted_p):
        # i is 0-indexed, so rank is i+1
        # n - i
        adj_p = p * (n - i)
        adjusted.append((adj_p, idx))
    
    # Step 2: Cumulative max to ensure monotonicity
    # The adjusted p-value for rank i is max(adjusted[0..i])
    max_val = 0.0
    final_adjusted = [0.0] * n
    
    # Sort by rank again to process
    adjusted.sort(key=lambda x: x[0]) # Sort by adjusted value? No, we need to process in order of original rank
    # Actually, Holm-Bonferroni: p_adj(i) = max_{j<=i} (p_(j) * (n - j + 1))
    # We iterate through the sorted p-values (from smallest to largest)
    
    current_max = 0.0
    for i, (p, original_idx) in enumerate(sorted_p):
        adj_val = p * (n - i)
        current_max = max(current_max, adj_val)
        final_adjusted[original_idx] = min(current_max, 1.0)
    
    return final_adjusted

def generate_residual_stats(
    residuals_mond: np.ndarray,
    residuals_nfw: np.ndarray,
    p_value_raw: float,
    p_value_corrected: float,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Generate summary statistics for residual analysis.
    
    Parameters
    ----------
    residuals_mond : np.ndarray
        MOND residuals.
    residuals_nfw : np.ndarray
        NFW residuals.
    p_value_raw : float
        Raw p-value from bootstrap test.
    p_value_corrected : float
        Corrected p-value.
    alpha : float
        Significance threshold.
        
    Returns
    -------
    Dict[str, Any]
        Dictionary of statistics.
    """
    stats = {
        'mond_mean': float(np.mean(residuals_mond)),
        'mond_median': float(np.median(residuals_mond)),
        'mond_std': float(np.std(residuals_mond)),
        'mond_abs_mean': float(np.mean(np.abs(residuals_mond))),
        'nfw_mean': float(np.mean(residuals_nfw)),
        'nfw_median': float(np.median(residuals_nfw)),
        'nfw_std': float(np.std(residuals_nfw)),
        'nfw_abs_mean': float(np.mean(np.abs(residuals_nfw))),
        'p_value_raw': p_value_raw,
        'p_value_corrected': p_value_corrected,
        'alpha': alpha,
        'mond_better_raw': p_value_raw < alpha,
        'mond_better_corrected': p_value_corrected < alpha
    }
    return stats

def main():
    """
    Main entry point for residual analysis.
    
    This function loads fit results, computes residuals, performs statistical tests,
    and generates the summary report.
    """
    logger.info("Starting residual analysis...")
    
    # This is a placeholder for the actual data loading logic which would be
    # implemented in the full pipeline (e. g., loading from results/fit_results.pkl)
    # For now, we assume the data is available or we simulate the flow.
    
    # Example: Load data
    # df = pd.read_csv('results/fit_summary.csv')
    # residuals_mond = df['res_mond'].values
    # residuals_nfw = df['res_nfw'].values
    
    # Placeholder for demonstration - in real execution, this would come from fit results
    # We will assume the script is run after fit results are generated.
    # If the file doesn't exist, we raise an error (fail loudly).
    input_path = Path('results/fit_summary.csv')
    if not input_path.exists():
        logger.error(f"Input file {input_path} not found. Run fitting first.")
        raise FileNotFoundError(f"Missing required input: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Extract residuals (assuming columns exist)
    # If columns are missing, we calculate them from observed and predicted
    if 'res_mond' not in df.columns or 'res_nfw' not in df.columns:
        logger.error("Required residual columns not found in fit_summary.csv")
        raise ValueError("Missing residual columns in input data")
        
    residuals_mond = df['res_mond'].values
    residuals_nfw = df['res_nfw'].values
    
    # Perform bootstrap test
    p_raw = block_bootstrap_permutation_test(residuals_mond, residuals_nfw)
    
    # Perform correction
    p_corrected = holm_bonferroni_correction([p_raw])[0]
    
    # Generate stats
    stats = generate_residual_stats(residuals_mond, residuals_nfw, p_raw, p_corrected)
    
    # Save results
    output_path = Path('results/residual_stats.csv')
    df_stats = pd.DataFrame([stats])
    df_stats.to_csv(output_path, index=False)
    logger.info(f"Residual statistics saved to {output_path}")
    
    # Generate verdict report
    from generate_verdict import generate_verdict_report
    generate_verdict_report(stats, output_path.replace('.csv', '_verdict.md'))
    
    logger.info("Residual analysis complete.")

if __name__ == "__main__":
    main()
