import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from src.config import load_config
from src.models.schemas import CorrelationResult

logger = logging.getLogger(__name__)

def calculate_spearman_correlation(diversity_df: pd.DataFrame, sleep_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Spearman rank correlation between diversity indices and sleep metrics.

    Args:
        diversity_df: DataFrame with sample_id and diversity indices (Shannon, Simpson, Observed OTUs)
        sleep_df: DataFrame with sample_id and sleep metrics (sleep_efficiency, sleep_duration_hours)

    Returns:
        DataFrame with correlation coefficients, p-values, and metadata
    """
    # Merge on sample_id
    merged = pd.merge(diversity_df, sleep_df, on='sample_id', how='inner')

    if len(merged) == 0:
        logger.warning("No overlapping samples between diversity and sleep data")
        return pd.DataFrame()

    results = []
    diversity_cols = ['shannon', 'simpson', 'observed_otus']
    sleep_cols = ['sleep_efficiency', 'sleep_duration_hours']

    for div_col in diversity_cols:
        for sleep_col in sleep_cols:
            if div_col not in merged.columns or sleep_col not in merged.columns:
                continue

            # Drop NaN pairs
            valid = merged[[div_col, sleep_col]].dropna()
            if len(valid) < 3:
                logger.warning(f"Not enough data points for {div_col} vs {sleep_col}")
                continue

            r, p = spearmanr(valid[div_col], valid[sleep_col])
            results.append({
                'diversity_metric': div_col,
                'sleep_metric': sleep_col,
                'r': r,
                'p': p,
                'n_samples': len(valid)
            })

    return pd.DataFrame(results) if results else pd.DataFrame()

def apply_benjamini_hochberg(df: pd.DataFrame, p_col: str = 'p') -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.

    Args:
        df: DataFrame with p-values
        p_col: Name of the p-value column

    Returns:
        DataFrame with added 'q' column for adjusted p-values
    """
    if df.empty or p_col not in df.columns:
        return df

    n = len(df)
    if n == 0:
        return df

    # Sort by p-value
    df_sorted = df.sort_values(p_col).reset_index(drop=True)
    ranks = np.arange(1, n + 1)

    # Calculate BH adjusted p-values
    q = (df_sorted[p_col] * n) / ranks
    q = np.minimum(q, 1.0)

    # Ensure monotonicity (cumulative minimum from bottom)
    q = np.minimum.accumulate(q[::-1])[::-1]

    df_sorted['q'] = q
    return df_sorted

def flag_correlations(df: pd.DataFrame, r_threshold: float = 0.3, q_threshold: float = 0.05) -> pd.DataFrame:
    """
    Flag correlations based on magnitude and significance.

    Args:
        df: DataFrame with 'r' and 'q' columns
        r_threshold: Absolute r-value threshold for "moderate" correlation
        q_threshold: q-value threshold for "meaningful" correlation

    Returns:
        DataFrame with 'is_moderate' and 'is_meaningful' columns
    """
    if df.empty:
        return df

    df = df.copy()
    df['is_moderate'] = df['r'].abs() > r_threshold
    df['is_meaningful'] = (df['q'] < q_threshold) & (df['r'].abs() > r_threshold)

    return df

def handle_no_significant_associations(df: pd.DataFrame, output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Handle the case where no significant associations are found.

    This function:
    1. Checks if the DataFrame is empty or has no meaningful correlations
    2. Adds a 'status' column indicating 'no_significant_associations' if applicable
    3. Ensures all required columns are present
    4. Optionally saves the result to a CSV file

    Args:
        df: DataFrame with correlation results (should have 'is_moderate' and 'is_meaningful' columns)
        output_path: Optional path to save the results CSV

    Returns:
        DataFrame with 'status' column added
    """
    if df.empty:
        logger.warning("No correlation results to process - returning empty DataFrame with status")
        df = pd.DataFrame(columns=['diversity_metric', 'sleep_metric', 'r', 'p', 'q', 'is_moderate', 'is_meaningful', 'status'])
        df['status'] = 'no_significant_associations'
        if output_path:
            df.to_csv(output_path, index=False)
        return df

    # Check if any correlations are meaningful
    meaningful_count = df['is_meaningful'].sum() if 'is_meaningful' in df.columns else 0

    if meaningful_count == 0:
        logger.info("No significant associations found. Marking all rows with 'no_significant_associations' status.")
        df = df.copy()
        df['status'] = 'no_significant_associations'
    else:
        # For rows that are meaningful, mark as 'significant', others as 'non_significant'
        df = df.copy()
        df['status'] = df['is_meaningful'].apply(lambda x: 'significant' if x else 'non_significant')

    # Ensure all required columns exist
    required_cols = ['diversity_metric', 'sleep_metric', 'r', 'p', 'q', 'is_moderate', 'is_meaningful', 'status']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    # Reorder columns
    df = df[required_cols]

    if output_path:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved correlation results to {output_path}")

    return df

def run_correlation_analysis(
    diversity_path: str,
    sleep_path: str,
    output_path: str,
    config: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Run the full correlation analysis pipeline.

    Args:
        diversity_path: Path to the diversity indices CSV
        sleep_path: Path to the sleep metrics CSV
        output_path: Path to save the correlation results CSV
        config: Optional configuration dictionary

    Returns:
        DataFrame with correlation results
    """
    logger.info("Starting correlation analysis...")

    # Load configuration
    if config is None:
        config = load_config()

    diversity_df = pd.read_csv(diversity_path)
    sleep_df = pd.read_csv(sleep_path)

    # Calculate correlations
    corr_df = calculate_spearman_correlation(diversity_df, sleep_df)

    if corr_df.empty:
        logger.warning("No correlations calculated. Handling empty case.")
        return handle_no_significant_associations(corr_df, Path(output_path))

    # Apply FDR correction
    corr_df = apply_benjamini_hochberg(corr_df)

    # Flag correlations
    corr_df = flag_correlations(corr_df)

    # Handle no significant associations case
    final_df = handle_no_significant_associations(corr_df, Path(output_path))

    return final_df

def main():
    """Main entry point for the correlation analysis script."""
    config = load_config()
    diversity_path = config.get('DIVERSITY_PATH', 'data/processed/diversity_indices.csv')
    sleep_path = config.get('SLEEP_PATH', 'data/processed/cleaned_microbiome_sleep.csv')
    output_path = config.get('CORRELATION_OUTPUT_PATH', 'data/processed/correlation_results.csv')

    result = run_correlation_analysis(diversity_path, sleep_path, output_path, config)
    logger.info(f"Correlation analysis complete. Results saved to {output_path}")

if __name__ == "__main__":
    main()
