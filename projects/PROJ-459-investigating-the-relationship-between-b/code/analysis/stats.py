"""
Statistical analysis module for brain-music preference correlation.
Implements Spearman correlations, Benjamini-Hochberg correction, and power analysis.
"""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, power
from statsmodels.stats.multitest import multipletests
from typing import Dict, List, Tuple, Optional, Union
import logging
from pathlib import Path
import json

from utils.io import save_json, save_parquet, ensure_dir
from config import get_derived_path
from data.models import CorrelationResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_spearman_correlations(metrics: pd.DataFrame, genres: pd.Series) -> pd.DataFrame:
    """
    Perform Spearman rank-order correlations between network metrics and genre preference scores.

    Args:
        metrics: DataFrame with subject_id as index (or column) and metric columns.
                 Expected columns: 'global_efficiency', 'modularity_Q', 'dynamic_reconfiguration_rate', etc.
        genres: Series with subject_id as index (or column) and genre preference scores.
                Expected columns: 'musical_genre' (or specific genre scores if available).

    Returns:
        DataFrame with columns: metric, genre, r (correlation), p_raw (raw p-value), p_adj (BH-corrected p-value)
    """
    logger.info(f"Computing Spearman correlations between {len(metrics.columns)} metrics and {len(genres.columns) if isinstance(genres, pd.DataFrame) else 1} genre scores")

    # Ensure alignment
    if isinstance(metrics.index, pd.RangeIndex):
        # If index is default, assume first column is subject_id or align by row order
        # For robustness, try to find a common key
        if 'subject_id' in metrics.columns:
            metrics = metrics.set_index('subject_id')
        if 'subject_id' in genres.columns:
            genres = genres.set_index('subject_id')
    
    # Align indices
    common_index = metrics.index.intersection(genres.index)
    if len(common_index) == 0:
        raise ValueError("No common subject IDs found between metrics and genres dataframes.")
    
    metrics_aligned = metrics.loc[common_index]
    genres_aligned = genres.loc[common_index]

    results = []
    metric_cols = [c for c in metrics_aligned.columns if c != 'subject_id']
    genre_cols = [c for c in genres_aligned.columns if c != 'subject_id']

    if not genre_cols:
        # Assume single column if no explicit column found and not a multi-index
        if isinstance(genres_aligned, pd.Series):
            genre_cols = ['score']
            genres_aligned = genres_aligned.to_frame(name='score')
        else:
            raise ValueError("No genre score columns found in genres DataFrame.")

    for metric_name in metric_cols:
        for genre_name in genre_cols:
            x = metrics_aligned[metric_name].dropna()
            y = genres_aligned[genre_name].loc[x.index]
            
            if len(x) < 3:
                logger.warning(f"Skipping {metric_name} vs {genre_name}: insufficient data points ({len(x)})")
                continue

            try:
                r, p_raw = spearmanr(x, y)
                results.append({
                    'metric': metric_name,
                    'genre': genre_name,
                    'r': r,
                    'p_raw': p_raw,
                    'n': len(x)
                })
            except Exception as e:
                logger.error(f"Error computing correlation for {metric_name} vs {genre_name}: {e}")
                continue

    if not results:
        logger.warning("No correlations computed. Returning empty DataFrame.")
        return pd.DataFrame(columns=['metric', 'genre', 'r', 'p_raw', 'n', 'p_adj'])

    df_results = pd.DataFrame(results)
    return df_results

def apply_bh_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg False Discovery Rate correction to raw p-values.

    Args:
        p_values: List of raw p-values.

    Returns:
        List of adjusted p-values.
    """
    if not p_values:
        return []
    
    try:
        # multipletests returns (reject, p_corrected, p_corrected, p_corrected)
        # We want the second return value (pvals_corrected)
        _, p_adj, _, _ = multipletests(p_values, method='fdr_bh')
        return list(p_adj)
    except Exception as e:
        logger.error(f"Error applying BH correction: {e}")
        return [1.0] * len(p_values)

def compute_power(sample_size: int, effect_size: float, alpha: float = 0.05) -> float:
    """
    Perform post-hoc power analysis for Spearman correlation.
    Target: power >= 0.8 for |r| >= 0.3.

    Args:
        sample_size: Number of subjects (N).
        effect_size: Expected correlation coefficient (r).
        alpha: Significance level (default 0.05).

    Returns:
        Calculated power (0.0 to 1.0).
    """
    if sample_size < 3:
        return 0.0
    
    try:
        # Using t-distribution approximation for correlation power
        # t = r * sqrt((n-2) / (1-r^2))
        # Power is calculated based on non-central t-distribution
        # Here we use a simplified approximation or scipy's power module if available for correlation
        # scipy.stats.power is for general tests, specific correlation power often uses specific formulas.
        # We will use the standard approximation:
        
        # Effect size for correlation is often treated as rho.
        # We can use the t-test power formula where the non-centrality parameter depends on rho.
        # However, scipy.stats.power does not directly have a 'correlation' test in older versions.
        # We will use the manual calculation based on the t-statistic distribution.
        
        # t = r * sqrt(n - 2) / sqrt(1 - r^2)
        # But for power analysis, we need the non-centrality parameter (nct).
        # nct = r * sqrt(n - 2) / sqrt(1 - r^2)
        # Power = 1 - CDF(t_crit, nct, df) - CDF(-t_crit, nct, df) ? 
        # Actually, for a two-tailed test:
        # Power = P(|T| > t_crit | H1)
        
        # Let's use a robust approximation or a library if available. 
        # Since we have statsmodels, we might rely on manual calculation or a helper.
        # Using the standard formula for power of correlation:
        
        # Fisher Z transformation approach:
        # z_r = 0.5 * ln((1+r)/(1-r))
        # SE = 1 / sqrt(n-3)
        # z_alpha = norm.ppf(1 - alpha/2)
        # Power = norm.cdf(z_r / SE - z_alpha) + norm.cdf(-z_r / SE - z_alpha)
        
        from scipy.stats import norm, t
        
        z_r = 0.5 * np.log((1 + abs(effect_size)) / (1 - abs(effect_size)))
        se = 1.0 / np.sqrt(sample_size - 3)
        z_alpha = norm.ppf(1 - alpha / 2)
        
        # Power calculation
        # Power = P(Z > z_alpha - z_r/SE) + P(Z < -z_alpha - z_r/SE)
        # Simplified for large N and effect:
        power_val = norm.cdf(z_r / se - z_alpha) + norm.cdf(-z_r / se - z_alpha)
        
        # Ensure bounds
        return float(max(0.0, min(1.0, power_val)))
        
    except Exception as e:
        logger.error(f"Error computing power: {e}")
        return 0.0

def flag_underpowered(power: float, threshold: float = 0.8) -> str:
    """
    Flag results as 'Underpowered' if power < threshold.

    Args:
        power: Calculated power value.
        threshold: Minimum acceptable power (default 0.8).

    Returns:
        String flag: 'Underpowered' or 'Adequate'.
    """
    if power < threshold:
        return "Underpowered"
    return "Adequate"

def run_null_distribution_validation(
    metrics: pd.DataFrame, 
    genres: pd.Series, 
    n_permutations: int = 1000, 
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run null distribution validation to verify false positive rate <= 0.05.
    Permutes the genre scores to break the relationship and re-compute correlations.

    Args:
        metrics: DataFrame of network metrics.
        genres: Series of genre scores.
        n_permutations: Number of permutations.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary with 'false_positive_rate', 'permutations_count', 'significant_count'.
    """
    if seed is not None:
        np.random.seed(seed)
    
    logger.info(f"Running null distribution validation with {n_permutations} permutations")
    
    # Align data
    common_index = metrics.index.intersection(genres.index)
    metrics_aligned = metrics.loc[common_index]
    genres_aligned = genres.loc[common_index]
    
    if len(common_index) < 3:
        return {'false_positive_rate': 0.0, 'permutations_count': 0, 'error': 'Insufficient data'}

    metric_cols = [c for c in metrics_aligned.columns if c != 'subject_id']
    genre_cols = [c for c in genres_aligned.columns if c != 'subject_id']
    if not genre_cols:
        genre_cols = ['score']
        genres_aligned = genres_aligned.to_frame(name='score')

    significant_count = 0
    total_tests = 0

    for _ in range(n_permutations):
        # Permute genres
        permuted_genres = genres_aligned[genre_cols[0]].sample(frac=1, random_state=None).reset_index(drop=True)
        permuted_genres.index = metrics_aligned.index
        
        # Compute correlation for each metric
        for metric_name in metric_cols:
            x = metrics_aligned[metric_name].dropna()
            y = permuted_genres.loc[x.index]
            
            if len(x) < 3:
                continue
                
            try:
                _, p_raw = spearmanr(x, y)
                total_tests += 1
                if p_raw < 0.05:
                    significant_count += 1
            except:
                continue

    if total_tests == 0:
        fpr = 0.0
    else:
        fpr = significant_count / total_tests

    report = {
        'false_positive_rate': fpr,
        'permutations_count': n_permutations,
        'significant_count': significant_count,
        'total_tests': total_tests,
        'threshold': 0.05
    }

    # Check against threshold
    if fpr > 0.05:
        logger.warning(f"False positive rate {fpr:.4f} exceeds threshold 0.05")
    else:
        logger.info(f"Null validation passed: FPR = {fpr:.4f}")

    return report

def save_correlation_results(
    results_df: pd.DataFrame, 
    power_report: Dict[str, float], 
    null_report: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> Path:
    """
    Save correlation results, power analysis, and null validation to disk.

    Args:
        results_df: DataFrame of correlation results.
        power_report: Dictionary of power analysis results.
        null_report: Dictionary of null validation results.
        output_dir: Output directory. Defaults to data/derived.

    Returns:
        Path to the saved CSV file.
    """
    if output_dir is None:
        output_dir = get_derived_path()
    
    ensure_dir(output_dir)
    
    # Apply BH correction to the results
    if not results_df.empty:
        p_values = results_df['p_raw'].tolist()
        adj_p_values = apply_bh_correction(p_values)
        results_df['p_adj'] = adj_p_values
    else:
        results_df['p_adj'] = []

    # Save main results
    results_path = output_dir / 'correlation_results.csv'
    results_df.to_csv(results_path, index=False)
    logger.info(f"Saved correlation results to {results_path}")

    # Save power report
    power_path = output_dir / 'power_analysis.json'
    save_json(power_report, power_path)
    logger.info(f"Saved power analysis to {power_path}")

    # Save null validation report
    null_path = output_dir / 'null_validation_report.json'
    save_json(null_report, null_path)
    logger.info(f"Saved null validation report to {null_path}")

    return results_path

def main():
    """
    Main entry point for statistical analysis.
    Loads metrics and genres data, computes correlations, and saves results.
    """
    logger.info("Starting statistical analysis pipeline")
    
    try:
        # Load data (Assuming preprocessed outputs exist from US2)
        # Path construction based on project structure
        metrics_path = get_derived_path() / 'network_metrics.csv'
        genres_path = get_derived_path() / 'genre_preferences.csv' # Or however it's stored

        if not metrics_path.exists():
            raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
        if not genres_path.exists():
            raise FileNotFoundError(f"Genres file not found: {genres_path}")

        metrics_df = pd.read_csv(metrics_path)
        genres_df = pd.read_csv(genres_path)

        # Convert to Series/DataFrame if needed
        if 'subject_id' in metrics_df.columns:
            metrics_df = metrics_df.set_index('subject_id')
        if 'subject_id' in genres_df.columns:
            genres_df = genres_df.set_index('subject_id')
        
        # Extract genre series (assuming single column of interest or specific column name)
        # If genres_df has multiple columns, we might need to iterate or select one
        # For this implementation, we assume the first numeric column or 'score'
        genre_col = 'musical_genre' if 'musical_genre' in genres_df.columns else genres_df.select_dtypes(include=[np.number]).columns[0]
        genres_series = genres_df[genre_col]

        # Compute correlations
        corr_results = compute_spearman_correlations(metrics_df, genres_series)
        
        # Power analysis (example: average effect size or max observed)
        if not corr_results.empty:
            avg_r = corr_results['r'].abs().mean()
            n = corr_results['n'].mean()
            power_val = compute_power(int(n), avg_r)
            flag = flag_underpowered(power_val)
            power_report = {
                'sample_size': int(n),
                'effect_size': float(avg_r),
                'power': float(power_val),
                'flag': flag,
                'threshold': 0.8
            }
        else:
            power_report = {'error': 'No correlations computed'}

        # Null validation
        null_report = run_null_distribution_validation(metrics_df, genres_series, n_permutations=1000)

        # Save results
        save_correlation_results(corr_results, power_report, null_report)

        logger.info("Statistical analysis completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise

if __name__ == "__main__":
    import sys
    sys.exit(main())
