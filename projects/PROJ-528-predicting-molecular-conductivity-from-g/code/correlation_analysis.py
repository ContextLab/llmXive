"""
Correlation Analysis Module.

Calculates Pearson correlations between features and the target variable,
computes p-values, and saves the results to a JSON file.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy.stats import pearsonr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_correlation_pvalues(
    df: pd.DataFrame,
    feature_columns: List[str],
    target_column: str
) -> Dict[str, Tuple[float, float]]:
    """
    Calculate Pearson correlation coefficient and p-value for each feature against the target.

    Args:
        df: DataFrame containing features and target.
        feature_columns: List of feature column names.
        target_column: Name of the target variable column.

    Returns:
        Dictionary mapping feature names to (correlation_coefficient, p_value).
    """
    results = {}

    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in DataFrame. "
                         f"Available columns: {list(df.columns)}")

    for feature in feature_columns:
        if feature not in df.columns:
            logger.warning(f"Feature '{feature}' not found in DataFrame. Skipping.")
            continue

        # Drop rows where either feature or target is NaN
        valid_data = df[[feature, target_column]].dropna()

        if len(valid_data) < 3:
            logger.warning(f"Not enough valid data points for feature '{feature}'. "
                           f"Skipping (n={len(valid_data)}).")
            results[feature] = (np.nan, np.nan)
            continue

        x = valid_data[feature].values
        y = valid_data[target_column].values

        try:
            corr, p_val = pearsonr(x, y)
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
        results: Dictionary of correlation results.
        output_path: Path to save the JSON file.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Convert tuples to lists for JSON serialization
    serializable_results = {
        feature: [corr, p_val]
        for feature, (corr, p_val) in results.items()
    }

    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)

    logger.info(f"Correlation results saved to {output_path}")


def main():
    """
    Main entry point for correlation analysis.
    Expects command-line arguments:
        --data: Path to the processed descriptors CSV.
        --target: Name of the target column (default: 'conductivity').
        --output: Path to save the correlation results JSON.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Calculate feature-target correlations and p-values."
    )
    parser.add_argument(
        '--data',
        type=str,
        required=True,
        help="Path to the processed descriptors CSV file."
    )
    parser.add_argument(
        '--target',
        type=str,
        default='conductivity',
        help="Name of the target column (default: 'conductivity')."
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help="Path to save the correlation results JSON file."
    )

    args = parser.parse_args()

    logger.info(f"Loading data from {args.data}")
    try:
        df = pd.read_csv(args.data)
    except FileNotFoundError:
        logger.error(f"Data file not found: {args.data}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        sys.exit(1)

    # Identify feature columns (all numeric columns except the target)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [col for col in numeric_cols if col != args.target]

    if not feature_cols:
        logger.error("No feature columns found in the dataset.")
        sys.exit(1)

    logger.info(f"Calculating correlations for {len(feature_cols)} features against '{args.target}'")
    results = calculate_correlation_pvalues(df, feature_cols, args.target)

    logger.info(f"Saving results to {args.output}")
    save_correlation_results(results, args.output)

    # Print summary
    significant = [f for f, (c, p) in results.items() if not np.isnan(p) and p < 0.05]
    logger.info(f"Found {len(significant)} features with p < 0.05: {significant[:5]}...")


if __name__ == "__main__":
    main()
