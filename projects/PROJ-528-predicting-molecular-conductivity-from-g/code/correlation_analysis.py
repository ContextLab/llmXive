import os
import json
import logging
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple, List, Optional

from code.logging_config import setup_logging

logger = setup_logging(__name__)

def calculate_correlation_pvalues(df: pd.DataFrame, target_col: str, feature_cols: Optional[List[str]] = None) -> Dict[str, Tuple[float, float]]:
    """
    Calculate Pearson correlation coefficients and p-values between features and the target variable.

    Args:
        df: DataFrame containing features and target.
        target_col: Name of the target column (e.g., 'conductivity', 'log_conductivity').
        feature_cols: List of feature column names. If None, all numeric columns except target are used.

    Returns:
        Dictionary mapping feature names to (correlation_coefficient, p_value) tuples.
    """
    if feature_cols is None:
        # Select all numeric columns excluding the target
        feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if target_col in feature_cols:
            feature_cols.remove(target_col)

    results = {}
    target_data = df[target_col].dropna()

    for feature in feature_cols:
        feature_data = df[feature].dropna()

        # Align indices to ensure we are comparing the same rows
        common_idx = target_data.index.intersection(feature_data.index)
        if len(common_idx) < 3:
            logger.warning(f"Insufficient data points for correlation between {feature} and {target_col}. Skipping.")
            results[feature] = (np.nan, np.nan)
            continue

        y = target_data.loc[common_idx]
        x = feature_data.loc[common_idx]

        try:
            corr, p_val = stats.pearsonr(x, y)
            results[feature] = (corr, p_val)
        except Exception as e:
            logger.warning(f"Failed to compute correlation for {feature}: {e}")
            results[feature] = (np.nan, np.nan)

    return results

def save_correlation_results(results: Dict[str, Tuple[float, float]], output_path: str) -> None:
    """
    Save correlation results to a JSON file.

    Args:
        results: Dictionary of correlation results.
        output_path: Path to the output JSON file.
    """
    # Convert tuple values to a serializable format (list or dict)
    serializable_results = {
        k: {"correlation": v[0], "p_value": v[1]} for k, v in results.items()
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    logger.info(f"Correlation results saved to {output_path}")

def load_correlation_results(input_path: str) -> Dict[str, Tuple[float, float]]:
    """
    Load correlation results from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        Dictionary of correlation results.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Correlation results file not found: {input_path}")

    with open(input_path, 'r') as f:
        data = json.load(f)

    # Convert back to tuple format
    return {k: (v["correlation"], v["p_value"]) for k, v in data.items()}

def main():
    """
    CLI entry point for correlation analysis.
    Expects a processed data file and outputs correlation results.
    """
    parser = argparse.ArgumentParser(description="Calculate feature-target correlations.")
    parser.add_argument("--input", type=str, default="data/processed/descriptors.csv",
                        help="Path to the input data file (CSV).")
    parser.add_argument("--target", type=str, default="log_conductivity",
                        help="Name of the target column.")
    parser.add_argument("--output", type=str, default="data/processed/correlation_results.json",
                        help="Path to the output JSON file.")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)

    if args.target not in df.columns:
        # Fallback: try to find a column containing 'conductivity' or 'gap'
        possible_targets = [c for c in df.columns if 'conductivity' in c.lower() or 'gap' in c.lower()]
        if possible_targets:
            args.target = possible_targets[0]
            logger.warning(f"Target '{args.target}' not found. Using '{args.target}' instead.")
        else:
            logger.error(f"Target column '{args.target}' not found in data.")
            sys.exit(1)

    logger.info(f"Calculating correlations with target: {args.target}")
    results = calculate_correlation_pvalues(df, args.target)

    logger.info(f"Saving results to {args.output}")
    save_correlation_results(results, args.output)

    # Print summary
    significant = [k for k, v in results.items() if not np.isnan(v[1]) and v[1] < 0.05]
    logger.info(f"Found {len(significant)} features with p-value < 0.05")

if __name__ == "__main__":
    import sys
    main()