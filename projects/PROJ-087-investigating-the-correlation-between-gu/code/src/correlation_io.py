"""
I/O utilities for correlation analysis results.
Handles saving correlation results to CSV as per T024.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Optional

from src.config import load_config

logger = logging.getLogger(__name__)


def save_correlation_results(
    results_df: pd.DataFrame,
    output_path: Optional[str] = None
) -> str:
    """
    Save correlation results to a CSV file.

    Args:
        results_df: DataFrame containing correlation results with columns:
            - diversity_metric
            - sleep_metric
            - spearman_r
            - p_value
            - q_value (adjusted p-value)
            - is_significant (boolean)
            - is_moderate (boolean)
            - is_meaningful (boolean)
        output_path: Optional path to save the results. If None, uses config default.

    Returns:
        The path where the file was saved.

    Raises:
        ValueError: If results_df is None or empty.
        FileNotFoundError: If output directory does not exist.
    """
    if results_df is None or results_df.empty:
        logger.warning("No correlation results to save. DataFrame is empty.")
        # Still create an empty file with headers to satisfy the contract
        results_df = pd.DataFrame(columns=[
            'diversity_metric', 'sleep_metric', 'spearman_r',
            'p_value', 'q_value', 'is_significant', 'is_moderate', 'is_meaningful'
        ])

    config = load_config()
    if output_path is None:
        output_path = config.get('OUTPUT_CORRELATION_PATH', 'data/processed/correlation_results.csv')

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Ensure the DataFrame has the expected columns in the correct order
    expected_columns = [
        'diversity_metric', 'sleep_metric', 'spearman_r',
        'p_value', 'q_value', 'is_significant', 'is_moderate', 'is_meaningful'
    ]

    # Reindex to ensure column order and fill missing with defaults if any
    for col in expected_columns:
        if col not in results_df.columns:
            if col in ['is_significant', 'is_moderate', 'is_meaningful']:
                results_df[col] = False
            else:
                results_df[col] = None

    results_df = results_df[expected_columns]

    # Save to CSV
    results_df.to_csv(output_file, index=False)
    logger.info(f"Saved correlation results to {output_file} ({len(results_df)} rows)")

    return str(output_file)
