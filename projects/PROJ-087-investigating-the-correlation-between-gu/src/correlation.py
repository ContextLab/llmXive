import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
from src.config import load_config

logger = logging.getLogger(__name__)

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.

    Parameters
    ----------
    p_values : List[float]
        List of raw p-values.
    alpha : float
        False discovery rate threshold (default 0.05).

    Returns
    -------
    List[float]
        List of adjusted q-values (FDR-corrected p-values).
    """
    if not p_values:
        return []

    n = len(p_values)
    # Sort p-values while keeping track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]

    # Calculate BH adjusted p-values
    # q_i = (n / i) * p_(i)
    # Then enforce monotonicity: q_i = min(q_i, q_{i+1}, ..., q_n)
    adjusted_p_values = [0.0] * n
    min_q = 1.0

    for i in range(n - 1, -1, -1):
        rank = i + 1
        q = (n / rank) * sorted_p_values[i]
        q = min(q, min_q)
        q = min(q, 1.0)  # Ensure q-value does not exceed 1
        min_q = q
        adjusted_p_values[i] = q

    # Map back to original order
    final_adjusted = [0.0] * n
    for i, adj in enumerate(adjusted_p_values):
        original_idx = sorted_indices[i]
        final_adjusted[original_idx] = adj

    return final_adjusted

def calculate_spearman_correlation(
    diversity_df: pd.DataFrame,
    sleep_metrics: List[str]
) -> pd.DataFrame:
    """
    Calculate Spearman rank correlation between diversity indices and sleep metrics.

    Parameters
    ----------
    diversity_df : pd.DataFrame
        DataFrame containing diversity indices (Shannon, Simpson, Observed OTUs)
        and sample IDs.
    sleep_metrics : List[str]
        List of sleep metric column names to correlate against.

    Returns
    -------
    pd.DataFrame
        DataFrame with correlation results including r, p, and q values.
    """
    results = []
    diversity_cols = [col for col in diversity_df.columns if col not in ['sample_id']]

    for div_col in diversity_cols:
        for sleep_col in sleep_metrics:
            # Drop rows with NaN in either column
            mask = diversity_df[div_col].notna() & diversity_df[sleep_col].notna()
            x = diversity_df.loc[mask, div_col]
            y = diversity_df.loc[mask, sleep_col]

            if len(x) < 3:
                logger.warning(f"Not enough data points for {div_col} vs {sleep_col}")
                continue

            r, p = spearmanr(x, y)
            results.append({
                'diversity_index': div_col,
                'sleep_metric': sleep_col,
                'r': r,
                'p_value': p
            })

    return pd.DataFrame(results)

def flag_correlations(df: pd.DataFrame, r_threshold: float = 0.3, q_threshold: float = 0.05) -> pd.DataFrame:
    """
    Flag correlations based on magnitude and significance.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'r' and 'q_value' columns.
    r_threshold : float
        Threshold for |r| to be considered moderate (default 0.3).
    q_threshold : float
        Threshold for q-value to be considered meaningful (default 0.05).

    Returns
    -------
    pd.DataFrame
        DataFrame with added 'is_moderate' and 'is_meaningful' columns.
    """
    df = df.copy()
    df['is_moderate'] = df['r'].abs() > r_threshold
    df['is_meaningful'] = (df['q_value'] < q_threshold) & (df['r'].abs() > r_threshold)
    return df

def handle_no_significant_associations(df: pd.DataFrame) -> bool:
    """
    Check if there are any meaningful associations.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'is_meaningful' column.

    Returns
    -------
    bool
        True if no meaningful associations found.
    """
    if df.empty:
        return True
    return not df['is_meaningful'].any()

def run_correlation_analysis(
    input_path: str,
    output_path: str,
    sleep_metrics: Optional[List[str]] = None
) -> None:
    """
    Run the full correlation analysis pipeline.

    Parameters
    ----------
    input_path : str
        Path to the cleaned microbiome/sleep dataset.
    output_path : str
        Path to save correlation results.
    sleep_metrics : List[str], optional
        List of sleep metrics to analyze. Defaults to ['sleep_efficiency', 'sleep_duration_hours'].
    """
    if sleep_metrics is None:
        sleep_metrics = ['sleep_efficiency', 'sleep_duration_hours']

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    # Calculate diversity indices if not present
    diversity_cols = [col for col in df.columns if col in ['shannon', 'simpson', 'observed_otus']]
    if not diversity_cols:
        logger.error("Diversity indices not found in input data. Run diversity analysis first.")
        raise ValueError("Diversity indices missing")

    logger.info(f"Calculating correlations for {len(diversity_cols)} diversity indices "
                f"against {len(sleep_metrics)} sleep metrics")

    corr_results = calculate_spearman_correlation(df, sleep_metrics)

    if corr_results.empty:
        logger.warning("No correlations calculated. Check data quality.")
        corr_results.to_csv(output_path, index=False)
        return

    # Apply BH correction
    p_values = corr_results['p_value'].tolist()
    q_values = apply_benjamini_hochberg(p_values)
    corr_results['q_value'] = q_values

    # Flag correlations
    corr_results = flag_correlations(corr_results)

    # Save results
    logger.info(f"Saving correlation results to {output_path}")
    corr_results.to_csv(output_path, index=False)

    meaningful_count = corr_results['is_meaningful'].sum()
    logger.info(f"Found {meaningful_count} meaningful correlations")

def main():
    """Main entry point for correlation analysis."""
    config = load_config()
    input_path = config.get('CLEANED_DATA_PATH', 'data/processed/cleaned_microbiome_sleep.csv')
    output_path = config.get('CORRELATION_OUTPUT_PATH', 'data/processed/correlation_results.csv')

    run_correlation_analysis(input_path, output_path)

if __name__ == "__main__":
    main()