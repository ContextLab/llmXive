import numpy as np
import pandas as pd
from scipy.stats import spearmanr, power
from statsmodels.stats.multitest import multipletests
from typing import Dict, List, Tuple, Optional, Union
import logging
from pathlib import Path

from utils.io import save_json, load_json, save_parquet, load_parquet
from config import get_derived_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_spearman_correlations(metrics: pd.DataFrame, genres: pd.Series) -> pd.DataFrame:
    """
    Compute Spearman correlations between network metrics and genre preference scores.
    
    Args:
        metrics: DataFrame with columns ['subject_id', 'metric_name', 'value']
        genres: Series indexed by subject_id with genre scores.
    
    Returns:
        DataFrame with columns ['metric', 'genre', 'r', 'p_raw']
    """
    logger.info("Computing Spearman correlations...")
    
    # Reshape metrics to wide format for correlation
    # Pivot metrics so rows are subjects and columns are metrics
    wide_metrics = metrics.pivot(index='subject_id', columns='metric_name', values='value')
    
    # Align with genres
    common_subjects = wide_metrics.index.intersection(genres.index)
    wide_metrics = wide_metrics.loc[common_subjects]
    aligned_genres = genres.loc[common_subjects]
    
    results = []
    
    for metric_name in wide_metrics.columns:
        metric_values = wide_metrics[metric_name]
        # Compute correlation for each genre if genres is a DataFrame, else single series
        if isinstance(aligned_genres, pd.DataFrame):
            for genre_col in aligned_genres.columns:
                r, p = spearmanr(metric_values, aligned_genres[genre_col])
                results.append({
                    'metric': metric_name,
                    'genre': genre_col,
                    'r': r,
                    'p_raw': p
                })
        else:
            # Single genre series
            r, p = spearmanr(metric_values, aligned_genres)
            results.append({
                'metric': metric_name,
                'genre': 'overall',
                'r': r,
                'p_raw': p
            })
    
    return pd.DataFrame(results)

def apply_bh_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction to raw p-values.
    
    Args:
        p_values: List of raw p-values.
    
    Returns:
        List of adjusted p-values.
    """
    logger.info("Applying Benjamini-Hochberg correction...")
    if len(p_values) == 0:
        return []
    
    # Use statsmodels method
    # reject, p_adjust, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    # We only need the adjusted p-values
    _, p_adjust, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    
    return p_adjust.tolist()

def compute_power(sample_size: int, effect_size: float, alpha: float = 0.05) -> float:
    """
    Perform post-hoc power analysis.
    
    Args:
        sample_size: Number of subjects.
        effect_size: Observed correlation (r).
        alpha: Significance level.
    
    Returns:
        Achieved power (probability of rejecting null if effect exists).
    """
    logger.info(f"Computing power for N={sample_size}, r={effect_size}...")
    
    # Convert r to Cohen's q or use t-test approximation for correlation
    # For Spearman, we approximate using Pearson power calculations
    # Using scipy.stats.power for correlation
    
    # Approximate using t-distribution for correlation
    # t = r * sqrt((n-2)/(1-r^2))
    # power = 1 - beta (probability of rejecting H0 given H1)
    
    # Use statsmodels or manual calculation
    # Here we use a simplified approximation
    if sample_size < 3 or abs(effect_size) >= 1.0:
        return 1.0 if abs(effect_size) >= 1.0 else 0.0
    
    # Manual approximation for power of correlation
    # Using the non-centrality parameter
    ncp = effect_size * np.sqrt(sample_size - 2) / np.sqrt(1 - effect_size**2)
    # Approximate power using normal approximation
    # This is a simplified version; in production use statsmodels.stats.power
    from scipy.stats import t
    
    # Critical t value for two-tailed test
    crit_t = t.ppf(1 - alpha/2, df=sample_size - 2)
    
    # Power is probability that t-stat > crit_t under non-central t
    # Approximation:
    power_val = 1 - t.cdf(crit_t, df=sample_size - 2, loc=ncp)
    # For two-tailed, add lower tail
    power_val += t.cdf(-crit_t, df=sample_size - 2, loc=ncp)
    
    return float(power_val)

def flag_underpowered(power: float, threshold: float = 0.8) -> str:
    """
    Flag results as 'Underpowered' if power < threshold.
    
    Args:
        power: Computed power value.
        threshold: Minimum acceptable power.
    
    Returns:
        'Underpowered' if below threshold, else 'Adequate'.
    """
    return 'Underpowered' if power < threshold else 'Adequate'

def run_null_distribution_validation(
    metrics: pd.DataFrame, 
    genres: pd.Series, 
    n_permutations: int = 1000
) -> Dict[str, Any]:
    """
    Run null distribution validation with permutations to estimate false positive rate.
    
    Args:
        metrics: DataFrame with metrics.
        genres: Series with genre scores.
        n_permutations: Number of permutations.
    
    Returns:
        Dictionary with 'false_positive_rate', 'permutations_count'.
    """
    logger.info(f"Running null distribution validation with {n_permutations} permutations...")
    
    # Compute observed correlations
    obs_results = compute_spearman_correlations(metrics, genres)
    
    # If no results, return empty
    if obs_results.empty:
        return {'false_positive_rate': 0.0, 'permutations_count': n_permutations}
    
    # Permutation test
    # Shuffle genres and recompute correlations
    # Count how many permutations yield |r| >= max(|observed|)
    
    observed_abs_r = obs_results['r'].abs().max()
    significant_count = 0
    
    for _ in range(n_permutations):
        # Shuffle genres
        shuffled_genres = genres.sample(frac=1.0, replace=False, random_state=None).reset_index(drop=True)
        # Re-align
        shuffled_results = compute_spearman_correlations(metrics, shuffled_genres)
        if shuffled_results['r'].abs().max() >= observed_abs_r:
            significant_count += 1
    
    fpr = significant_count / n_permutations
    
    return {
        'false_positive_rate': fpr,
        'permutations_count': n_permutations
    }

def save_correlation_results(results: pd.DataFrame, output_path: Optional[str] = None) -> Path:
    """
    Save correlation results to Parquet.
    
    Args:
        results: DataFrame with correlation results.
        output_path: Optional path. Defaults to derived/correlation_results.parquet.
    
    Returns:
        Path to saved file.
    """
    if output_path is None:
        output_path = get_derived_path() / 'correlation_results.parquet'
    else:
        output_path = Path(output_path)
    
    save_parquet(results, output_path)
    logger.info(f"Saved correlation results to {output_path}")
    return output_path

def main():
    """Main entry point for stats module (for testing/CLI)."""
    logger.info("Stats module main called.")
    # In a real scenario, this would load data and run the pipeline
    pass

if __name__ == '__main__':
    main()
