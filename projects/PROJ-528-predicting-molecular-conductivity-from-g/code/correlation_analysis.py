"""
Correlation Analysis Module for Molecular Conductivity Project.

This module implements the calculation of Pearson correlations between features
and the target variable (conductivity or HOMO-LUMO gap), including p-value
calculation and result persistence.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

def calculate_correlation_pvalues(
    data: pd.DataFrame,
    target_col: str,
    feature_cols: Optional[List[str]] = None
) -> Dict[str, Tuple[float, float]]:
    """
    Calculate Pearson correlation coefficients and p-values for features vs target.

    Args:
        data: DataFrame containing features and target variable.
        target_col: Name of the target column (e.g., 'conductivity', 'log_conductivity').
        feature_cols: Optional list of feature columns to analyze. If None, uses all
                      numeric columns except the target.

    Returns:
        Dictionary mapping feature names to (correlation_coefficient, p_value) tuples.

    Raises:
        ValueError: If target column is not found or if data is empty.
    """
    if target_col not in data.columns:
        raise ValueError(f"Target column '{target_col}' not found in data. "
                       f"Available columns: {list(data.columns)}")

    if feature_cols is None:
        # Select all numeric columns except the target
        feature_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        if target_col in feature_cols:
            feature_cols.remove(target_col)

    if not feature_cols:
        logger.warning("No feature columns found for correlation analysis.")
        return {}

    results = {}
    logger.info(f"Calculating correlations for {len(feature_cols)} features against '{target_col}'")

    for feature in feature_cols:
        x = data[feature].dropna()
        y = data[target_col].loc[x.index].dropna()

        # Ensure we have matching non-NaN pairs
        if len(x) == 0 or len(y) == 0:
            logger.warning(f"Skipping '{feature}': no valid data pairs with target.")
            continue

        if len(x) != len(y):
            # Re-align after dropna
            mask = ~(data[feature].isna() | data[target_col].isna())
            x = data.loc[mask, feature]
            y = data.loc[mask, target_col]

        if len(x) < 2:
            logger.warning(f"Skipping '{feature}': insufficient data points ({len(x)}) for correlation.")
            continue

        try:
            corr, p_val = stats.pearsonr(x, y)
            if not np.isfinite(corr) or not np.isfinite(p_val):
                logger.warning(f"Non-finite correlation/p-value for '{feature}'. Setting to NaN.")
                results[feature] = (np.nan, np.nan)
            else:
                results[feature] = (float(corr), float(p_val))
        except Exception as e:
            logger.error(f"Error calculating correlation for '{feature}': {e}")
            results[feature] = (np.nan, np.nan)

    return results

def save_correlation_results(
    results: Dict[str, Tuple[float, float]],
    output_path: str
) -> None:
    """
    Save correlation results to a JSON file.

    Args:
        results: Dictionary of correlation results from calculate_correlation_pvalues.
        output_path: Path to save the JSON file.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Convert tuples to lists for JSON serialization
    serializable_results = {
        feature: [float(corr), float(p_val)]
        for feature, (corr, p_val) in results.items()
    }

    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)

    logger.info(f"Saved correlation results to {output_path}")

def load_correlation_results(input_path: str) -> Dict[str, Tuple[float, float]]:
    """
    Load correlation results from a JSON file.

    Args:
        input_path: Path to the JSON file containing results.

    Returns:
        Dictionary mapping feature names to (correlation_coefficient, p_value) tuples.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Correlation results file not found: {input_path}")

    with open(input_path, 'r') as f:
        data = json.load(f)

    return {
        feature: (float(corr), float(p_val))
        for feature, (corr, p_val) in data.items()
    }

def main():
    """
    Main entry point for correlation analysis script.
    Expects command-line arguments:
      --data: Path to processed data CSV (e.g., data/processed/descriptors.csv)
      --target: Name of target column (default: 'log_conductivity' or 'conductivity')
      --output: Path to save correlation results JSON
    """
    import argparse

    parser = argparse.ArgumentParser(description="Calculate feature-target correlations.")
    parser.add_argument("--data", type=str, required=True, help="Path to input data CSV")
    parser.add_argument("--target", type=str, default=None, help="Target column name")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    logger.info(f"Loading data from {args.data}")
    try:
        data = pd.read_csv(args.data)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Determine target column if not specified
    target_col = args.target
    if target_col is None:
        if 'log_conductivity' in data.columns:
            target_col = 'log_conductivity'
        elif 'conductivity' in data.columns:
            target_col = 'conductivity'
        else:
            logger.error("No target column specified and could not auto-detect.")
            sys.exit(1)

    logger.info(f"Using target column: {target_col}")

    # Calculate correlations
    results = calculate_correlation_pvalues(data, target_col)

    if not results:
        logger.warning("No correlations calculated. Check data and target column.")
        # Still save empty results to avoid downstream failures
        save_correlation_results(results, args.output)
        return

    logger.info(f"Calculated {len(results)} correlations. Range: "
              f"[{min(r[0] for r in results.values()):.3f}, "
              f"{max(r[0] for r in results.values()):.3f}]")

    # Save results
    save_correlation_results(results, args.output)
    logger.info("Correlation analysis complete.")

if __name__ == "__main__":
    main()
