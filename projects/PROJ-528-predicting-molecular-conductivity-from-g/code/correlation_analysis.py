"""
Correlation Analysis Module for T041.

Implements calculation of feature-target correlations with p-values using
scipy.stats.pearsonr as required by FR-005.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)

def calculate_correlation_pvalues(
    df: pd.DataFrame,
    feature_columns: List[str],
    target_column: str
) -> Dict[str, Tuple[float, float]]:
    """
    Calculate Pearson correlation coefficients and p-values between features and target.

    Args:
        df: DataFrame containing features and target.
        feature_columns: List of feature column names to analyze.
        target_column: Name of the target variable column.

    Returns:
        Dictionary mapping feature names to (correlation_coefficient, p_value).
        If a feature has zero variance or is constant, returns (np.nan, np.nan).

    Raises:
        ValueError: If target column is missing or if input data is invalid.
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in DataFrame. Available columns: {list(df.columns)}")

    results = {}

    for col in feature_columns:
        if col not in df.columns:
            logger.warning(f"Feature column '{col}' not found in DataFrame. Skipping.")
            continue

        x = df[col].dropna()
        y = df[target_column].loc[x.index].dropna()

        # Align indices after dropping NaNs
        valid_mask = ~x.isna() & ~y.isna()
        x_clean = x[valid_mask]
        y_clean = y[valid_mask]

        if len(x_clean) < 2:
            logger.warning(f"Insufficient data for feature '{col}' (n={len(x_clean)}). Skipping.")
            results[col] = (np.nan, np.nan)
            continue

        # Check for zero variance
        if x_clean.std() == 0 or y_clean.std() == 0:
            logger.warning(f"Zero variance detected for '{col}' or target. Correlation undefined.")
            results[col] = (np.nan, np.nan)
            continue

        try:
            corr, p_val = stats.pearsonr(x_clean, y_clean)
            results[col] = (float(corr), float(p_val))
        except Exception as e:
            logger.error(f"Error calculating correlation for '{col}': {e}")
            results[col] = (np.nan, np.nan)

    return results

def save_correlation_results(
    results: Dict[str, Tuple[float, float]],
    output_path: str
) -> None:
    """
    Save correlation results to a JSON file.

    Args:
        results: Dictionary of correlation results.
        output_path: Path to save the JSON file.
    """
    # Convert tuples to lists for JSON serialization
    serializable_results = {
        feature: {"correlation": corr, "p_value": p_val}
        for feature, (corr, p_val) in results.items()
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    logger.info(f"Correlation results saved to {output_path}")

def main():
    """
    Main entry point for running correlation analysis.
    Expects --data and --output arguments.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Calculate feature-target correlations.")
    parser.add_argument("--data", type=str, required=True, help="Path to input CSV file with features and target.")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file for correlation results.")
    parser.add_argument("--target", type=str, default="conductivity", help="Name of the target column.")
    args = parser.parse_args()

    # Setup logging
    from code.logging_config import setup_logging
    setup_logging()

    logger.info(f"Loading data from {args.data}")
    df = pd.read_csv(args.data)

    # Identify feature columns (exclude 'smiles', 'status', and target)
    exclude_cols = ['smiles', 'status', args.target]
    feature_cols = [col for col in df.columns if col not in exclude_cols]

    if not feature_cols:
        logger.error("No feature columns found to analyze.")
        return

    logger.info(f"Analyzing {len(feature_cols)} features against target '{args.target}'")
    results = calculate_correlation_pvalues(df, feature_cols, args.target)

    # Save results
    save_correlation_results(results, args.output)

    # Print summary
    significant = [k for k, v in results.items() if not np.isnan(v[1]) and v[1] < 0.05]
    logger.info(f"Found {len(significant)} features with p-value < 0.05: {significant}")

if __name__ == "__main__":
    main()
