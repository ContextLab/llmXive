import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import json

from src.config import load_config
from src.logging_config import setup_logger

logger = setup_logger(__name__)

def calculate_spearman_correlation(
    diversity_df: pd.DataFrame,
    sleep_metrics: List[str],
    diversity_cols: List[str]
) -> pd.DataFrame:
    """
    Calculate Spearman rank correlation between diversity indices and sleep metrics.

    Args:
        diversity_df: DataFrame containing diversity indices and sleep metrics.
        sleep_metrics: List of sleep metric column names.
        diversity_cols: List of diversity index column names.

    Returns:
        DataFrame with correlation results (r, p-value).
    """
    results = []

    for div_col in diversity_cols:
        for sleep_col in sleep_metrics:
            if div_col not in diversity_df.columns or sleep_col not in diversity_df.columns:
                logger.warning(f"Columns {div_col} or {sleep_col} not found in DataFrame. Skipping.")
                continue

            # Drop rows with missing values in either column
            valid_data = diversity_df[[div_col, sleep_col]].dropna()

            if len(valid_data) < 3:
                logger.warning(f"Not enough data points for {div_col} vs {sleep_col}. Skipping.")
                continue

            r, p_value = spearmanr(valid_data[div_col], valid_data[sleep_col])

            results.append({
                'diversity_metric': div_col,
                'sleep_metric': sleep_col,
                'correlation_coefficient': r,
                'p_value': p_value
            })

    return pd.DataFrame(results)

def apply_benjamini_hochberg(
    results_df: pd.DataFrame,
    p_value_col: str = 'p_value'
) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.

    Args:
        results_df: DataFrame with p-values.
        p_value_col: Name of the column containing p-values.

    Returns:
        DataFrame with an additional 'q_value' column.
    """
    if results_df.empty:
        results_df['q_value'] = []
        return results_df

    p_values = results_df[p_value_col].values
    n = len(p_values)

    if n == 0:
        results_df['q_value'] = []
        return results_df

    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]

    # Calculate BH adjusted p-values
    q_values = np.zeros(n)
    for i in range(n):
        rank = i + 1
        q_values[sorted_indices[i]] = sorted_p_values[i] * n / rank

    # Ensure q-values are monotonically increasing (from smallest to largest rank)
    # We iterate backwards to ensure this
    for i in range(n - 2, -1, -1):
        if q_values[sorted_indices[i]] > q_values[sorted_indices[i + 1]]:
            q_values[sorted_indices[i]] = q_values[sorted_indices[i + 1]]

    # Clip q-values to [0, 1]
    q_values = np.clip(q_values, 0, 1)

    results_df['q_value'] = q_values
    return results_df

def flag_correlations(
    results_df: pd.DataFrame,
    r_threshold: float = 0.3,
    q_threshold: float = 0.05
) -> pd.DataFrame:
    """
    Flag correlations based on magnitude and significance thresholds.

    Args:
        results_df: DataFrame with correlation results including 'correlation_coefficient' and 'q_value'.
        r_threshold: Absolute correlation coefficient threshold for "moderate".
        q_threshold: Q-value threshold for "meaningful".

    Returns:
        DataFrame with added 'is_moderate' and 'is_meaningful' boolean columns.
    """
    if results_df.empty:
        results_df['is_moderate'] = []
        results_df['is_meaningful'] = []
        return results_df

    results_df['is_moderate'] = results_df['correlation_coefficient'].abs() > r_threshold
    results_df['is_meaningful'] = (results_df['q_value'] < q_threshold) & results_df['is_moderate']

    return results_df

def handle_no_significant_associations(
    results_df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Handle the case where no significant associations are found.

    This function:
    1. Checks if the results DataFrame is empty or has no meaningful correlations.
    2. Logs a clear message explaining the situation.
    3. If output_path is provided, writes a summary JSON file indicating no findings.
    4. Returns a dictionary summarizing the outcome.

    Args:
        results_df: DataFrame containing correlation results.
        output_path: Optional Path to save a JSON summary of the "no association" case.

    Returns:
        Dictionary with keys: 'found_meaningful' (bool), 'total_tested' (int), 'meaningful_count' (int), 'message' (str).
    """
    total_tested = len(results_df)
    meaningful_count = 0
    found_meaningful = False

    if not results_df.empty and 'is_meaningful' in results_df.columns:
        meaningful_count = int(results_df['is_meaningful'].sum())
        found_meaningful = meaningful_count > 0

    if not found_meaningful:
        msg = "No significant associations found: No correlations met the criteria (|r| > 0.3 and q-value < 0.05)."
        logger.info(msg)

        summary = {
            'found_meaningful': False,
            'total_tested': total_tested,
            'meaningful_count': 0,
            'message': msg,
            'timestamp': pd.Timestamp.now().isoformat()
        }
    else:
        msg = f"Found {meaningful_count} meaningful associations out of {total_tested} tests."
        logger.info(msg)
        summary = {
            'found_meaningful': True,
            'total_tested': total_tested,
            'meaningful_count': meaningful_count,
            'message': msg,
            'timestamp': pd.Timestamp.now().isoformat()
        }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"No significant associations summary saved to {output_path}")

    return summary

def run_correlation_analysis(
    input_path: Path,
    output_csv_path: Path,
    diversity_cols: List[str],
    sleep_cols: List[str],
    r_threshold: float = 0.3,
    q_threshold: float = 0.05
) -> pd.DataFrame:
    """
    Run the full correlation analysis pipeline.

    Args:
        input_path: Path to the cleaned dataset CSV.
        output_csv_path: Path to save the correlation results CSV.
        diversity_cols: List of diversity metric column names.
        sleep_cols: List of sleep metric column names.
        r_threshold: Threshold for moderate correlation.
        q_threshold: Threshold for significance.

    Returns:
        DataFrame with correlation results.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    logger.info("Calculating Spearman correlations")
    corr_results = calculate_spearman_correlation(df, sleep_cols, diversity_cols)

    if corr_results.empty:
        logger.warning("No correlations could be calculated. The result DataFrame is empty.")
        corr_results.to_csv(output_csv_path, index=False)
        return corr_results

    logger.info("Applying Benjamini-Hochberg correction")
    corr_results = apply_benjamini_hochberg(corr_results)

    logger.info("Flagging correlations")
    corr_results = flag_correlations(corr_results, r_threshold, q_threshold)

    logger.info(f"Saving results to {output_csv_path}")
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    corr_results.to_csv(output_csv_path, index=False)

    return corr_results

def main():
    """Main entry point for correlation analysis."""
    config = load_config()
    input_path = Path(config.get('DATA_PROCESSED', 'data/processed')) / 'cleaned_microbiome_sleep.csv'
    output_path = Path(config.get('DATA_PROCESSED', 'data/processed')) / 'correlation_results.csv'

    diversity_cols = ['shannon', 'simpson', 'observed_otus']
    sleep_cols = ['sleep_efficiency', 'sleep_duration_hours', 'wake_after_sleep_onset']

    # Run analysis
    results = run_correlation_analysis(
        input_path=input_path,
        output_csv_path=output_path,
        diversity_cols=diversity_cols,
        sleep_cols=sleep_cols
    )

    # Handle "no significant associations" case
    no_assoc_path = Path(config.get('DATA_PROCESSED', 'data/processed')) / 'correlation_no_associations.json'
    summary = handle_no_significant_associations(results, no_assoc_path)

    if not summary['found_meaningful']:
        logger.warning("Pipeline completed with no significant findings. Review logs and summary JSON.")
    else:
        logger.info(f"Pipeline completed. Found {summary['meaningful_count']} meaningful associations.")

if __name__ == '__main__':
    main()