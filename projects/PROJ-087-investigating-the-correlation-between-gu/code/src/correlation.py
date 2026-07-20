import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import json
import os
import sys

# Add parent directory to path to allow imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config
from src.logging_config import setup_logger

logger = setup_logger(__name__)

def calculate_spearman_correlation(diversity_df: pd.DataFrame, sleep_metrics: List[str]) -> pd.DataFrame:
    """
    Calculate Spearman rank correlation between diversity indices and sleep metrics.

    Args:
        diversity_df: DataFrame containing diversity indices (Shannon, Simpson, etc.) and sample IDs
        sleep_metrics: List of sleep metric column names to correlate against

    Returns:
        DataFrame with correlation coefficients, p-values, and metadata
    """
    results = []

    # Ensure diversity_df has required columns
    required_cols = ['sample_id', 'shannon', 'simpson', 'observed_otus']
    for col in required_cols:
        if col not in diversity_df.columns:
            logger.error(f"Missing required column: {col}")
            raise ValueError(f"Missing required column: {col}")

    for sleep_metric in sleep_metrics:
        if sleep_metric not in diversity_df.columns:
            logger.warning(f"Sleep metric {sleep_metric} not found in dataframe, skipping.")
            continue

        for diversity_metric in ['shannon', 'simpson', 'observed_otus']:
            # Drop rows with NaN in either column
            valid_data = diversity_df[[diversity_metric, sleep_metric]].dropna()

            if len(valid_data) < 3:
                logger.warning(f"Not enough data points for {diversity_metric} vs {sleep_metric}")
                continue

            r, p_value = spearmanr(valid_data[diversity_metric], valid_data[sleep_metric])

            results.append({
                'diversity_metric': diversity_metric,
                'sleep_metric': sleep_metric,
                'correlation_coefficient': r,
                'p_value': p_value,
                'n_samples': len(valid_data)
            })

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results)

def apply_benjamini_hochberg(results_df: pd.DataFrame, p_value_col: str = 'p_value') -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.

    Args:
        results_df: DataFrame containing p-values
        p_value_col: Name of the column containing p-values

    Returns:
        DataFrame with added 'q_value' column
    """
    if results_df.empty:
        return results_df.copy()

    df = results_df.copy()
    df = df.sort_values(p_value_col)

    n = len(df)
    df['rank'] = range(1, n + 1)
    df['q_value'] = (df[p_value_col] * n) / df['rank']

    # Ensure q-values are monotonic (cumulative min from bottom)
    df['q_value'] = df['q_value'].iloc[::-1].cummin().iloc[::-1]

    # Cap q-values at 1.0
    df['q_value'] = df['q_value'].clip(upper=1.0)

    return df.drop(columns=['rank'])

def flag_correlations(results_df: pd.DataFrame, 
                      r_threshold: float = 0.3, 
                      q_threshold: float = 0.05) -> pd.DataFrame:
    """
    Flag correlations as moderate or meaningful based on thresholds.

    Args:
        results_df: DataFrame with correlation results including 'correlation_coefficient' and 'q_value'
        r_threshold: Absolute correlation coefficient threshold for "moderate"
        q_threshold: Q-value threshold for "meaningful"

    Returns:
        DataFrame with added 'is_moderate' and 'is_meaningful' boolean columns
    """
    if results_df.empty:
        return results_df.copy()

    df = results_df.copy()
    df['is_moderate'] = df['correlation_coefficient'].abs() > r_threshold
    df['is_meaningful'] = (df['q_value'] < q_threshold) & (df['correlation_coefficient'].abs() > r_threshold)

    return df

def handle_no_significant_associations(results_df: pd.DataFrame, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Handle the case where no significant associations are found.
    
    This function:
    1. Checks if the input DataFrame is empty or contains no meaningful correlations.
    2. Logs a clear message about the absence of significant findings.
    3. Optionally saves a summary report to a JSON file indicating no significant associations.
    4. Returns a status dictionary for downstream processing or reporting.

    Args:
        results_df: DataFrame containing correlation results (may be empty or have no meaningful flags)
        output_path: Optional path to save a JSON report of the "no association" finding

    Returns:
        Dictionary containing:
            - 'has_significant_associations': bool
            - 'total_tests': int
            - 'meaningful_count': int
            - 'message': str
            - 'report_path': str or None
    """
    if results_df.empty:
        has_significant = False
        total_tests = 0
        meaningful_count = 0
        message = "No correlation tests were performed (input data was empty)."
    else:
        # Ensure 'is_meaningful' column exists
        if 'is_meaningful' not in results_df.columns:
            # If not flagged yet, we can't determine meaningfulness without thresholds
            # For safety, assume not meaningful if not flagged
            meaningful_count = 0
        else:
            meaningful_count = int(results_df['is_meaningful'].sum())
        
        total_tests = len(results_df)
        has_significant = meaningful_count > 0

        if has_significant:
            message = f"Found {meaningful_count} meaningful associations out of {total_tests} tests."
        else:
            message = "No significant associations found (q-value < 0.05 AND |r| > 0.3)."

    logger.info(message)

    report = {
        'has_significant_associations': has_significant,
        'total_tests': total_tests,
        'meaningful_count': meaningful_count,
        'message': message,
        'timestamp': pd.Timestamp.now().isoformat()
    }

    if output_path and not has_significant:
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Saved no-association report to: {output_path}")
            report['report_path'] = output_path
        except Exception as e:
            logger.error(f"Failed to write report to {output_path}: {e}")
            report['report_path'] = None
    else:
        report['report_path'] = None

    return report

def run_correlation_analysis(input_path: str, 
                             output_csv_path: str, 
                             output_report_path: Optional[str] = None,
                             r_threshold: float = 0.3, 
                             q_threshold: float = 0.05) -> Dict[str, Any]:
    """
    Run the full correlation analysis pipeline:
    1. Load cleaned data
    2. Calculate Spearman correlations
    3. Apply Benjamini-Hochberg correction
    4. Flag significant correlations
    5. Handle "no significant associations" case
    6. Save results to CSV and optional JSON report

    Args:
        input_path: Path to cleaned microbiome-sleep CSV
        output_csv_path: Path to save correlation results CSV
        output_report_path: Path to save "no association" JSON report (optional)
        r_threshold: Threshold for moderate correlation
        q_threshold: Threshold for meaningful correlation

    Returns:
        Dictionary with analysis summary and file paths
    """
    config = load_config()
    logger.info(f"Starting correlation analysis from {input_path}")

    # Load data
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} samples")

    sleep_metrics = ['sleep_efficiency', 'sleep_duration_hours', 'wake_after_sleep_onset']
    sleep_metrics = [m for m in sleep_metrics if m in df.columns]

    if not sleep_metrics:
        logger.error("No valid sleep metrics found in input data.")
        raise ValueError("No valid sleep metrics found in input data.")

    # Calculate correlations
    corr_results = calculate_spearman_correlation(df, sleep_metrics)

    if corr_results.empty:
        logger.warning("Correlation calculation returned empty results.")
        # Handle empty case
        report = handle_no_significant_associations(pd.DataFrame(), output_report_path)
        # Save empty results
        pd.DataFrame(columns=['diversity_metric', 'sleep_metric', 'correlation_coefficient', 
                              'p_value', 'q_value', 'is_moderate', 'is_meaningful']).to_csv(output_csv_path, index=False)
        return report

    # Apply FDR correction
    corr_results = apply_benjamini_hochberg(corr_results)

    # Flag correlations
    corr_results = flag_correlations(corr_results, r_threshold, q_threshold)

    # Handle no significant associations
    report = handle_no_significant_associations(corr_results, output_report_path)

    # Save results
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    corr_results.to_csv(output_csv_path, index=False)
    logger.info(f"Saved correlation results to {output_csv_path}")

    report['output_csv_path'] = output_csv_path
    return report

def main():
    """Main entry point for correlation analysis script."""
    config = load_config()
    input_path = config.get('PROCESSED_DATA_PATH', 'data/processed/cleaned_microbiome_sleep.csv')
    output_csv = config.get('CORRELATION_OUTPUT_PATH', 'data/processed/correlation_results.csv')
    output_report = config.get('NO_ASSOCIATION_REPORT_PATH', 'data/processed/no_association_report.json')

    try:
        result = run_correlation_analysis(
            input_path=input_path,
            output_csv_path=output_csv,
            output_report_path=output_report
        )
        logger.info("Correlation analysis completed successfully.")
        logger.info(f"Has significant associations: {result['has_significant_associations']}")
        if not result['has_significant_associations']:
            logger.info(result['message'])
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()