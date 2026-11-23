import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
import logging
from scipy import stats
from statsmodels.stats.multitest import multipletests

logger = logging.getLogger(__name__)

def calculate_correlation_pvalues(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: Optional[List[str]] = None
) -> List[Tuple[str, float, float]]:
    """
    Calculate Pearson correlation coefficients and p-values between features and target.

    Args:
        df: DataFrame containing features and target.
        target_col: Name of the target column.
        feature_cols: List of feature columns to analyze. If None, all numeric columns
                      excluding target are used.

    Returns:
        List of tuples (feature_name, correlation_coefficient, p_value).
    """
    if feature_cols is None:
        # Select all numeric columns excluding the target
        feature_cols = df.select_dtypes(include=[np.number]).columns.drop(target_col).tolist()

    results = []
    for col in feature_cols:
        if col not in df.columns:
            logger.warning(f"Feature {col} not found in DataFrame, skipping.")
            continue

        # Drop rows where either feature or target is NaN
        valid_mask = df[[col, target_col]].notna().all(axis=1)
        x = df.loc[valid_mask, col].values
        y = df.loc[valid_mask, target_col].values

        if len(x) < 3:
            logger.warning(f"Not enough data points for {col}, skipping.")
            continue

        corr, p_val = stats.pearsonr(x, y)
        results.append((col, corr, p_val))

    return results

def benjamini_hochberg(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.

    Args:
        p_values: List of p-values to correct.
        alpha: Significance level (default 0.05).

    Returns:
        Tuple of (adjusted_p_values, rejection_mask).
        adjusted_p_values: List of adjusted p-values.
        rejection_mask: List of booleans indicating if the null hypothesis is rejected.
    """
    if not p_values:
        return [], []

    # Use statsmodels multipletests for robust BH correction
    # method='fdr_bh' implements the Benjamini-Hochberg procedure
    reject, pvals_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')

    return pvals_corrected.tolist(), reject.tolist()

def apply_bh_correction_to_df(
    correlation_results: List[Tuple[str, float, float]],
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg correction to correlation results and return a DataFrame.

    Args:
        correlation_results: List of (feature, corr, p_value) tuples.
        alpha: Significance level.

    Returns:
        DataFrame with columns: feature, correlation, p_value, adjusted_p_value, is_significant.
    """
    if not correlation_results:
        return pd.DataFrame(columns=['feature', 'correlation', 'p_value', 'adjusted_p_value', 'is_significant'])

    df = pd.DataFrame(correlation_results, columns=['feature', 'correlation', 'p_value'])

    # Extract p-values for correction
    p_values = df['p_value'].tolist()

    # Apply BH correction
    adjusted_p_values, is_significant = benjamini_hochberg(p_values, alpha)

    df['adjusted_p_value'] = adjusted_p_values
    df['is_significant'] = is_significant

    # Sort by adjusted p-value (ascending) then by feature name
    df = df.sort_values(by=['adjusted_p_value', 'feature']).reset_index(drop=True)

    return df

def main():
    """
    CLI entry point for feature analysis with BH correction.
    """
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Apply Benjamini-Hochberg correction to feature correlations.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/descriptors.csv",
        help="Path to input descriptors CSV."
    )
    parser.add_argument(
        "--target",
        type=str,
        default="conductivity",
        help="Name of the target column."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/correlation_bh_results.csv",
        help="Path to output CSV with BH corrected results."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for FDR correction."
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Load data
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        return 1

    df = pd.read_csv(args.input)

    # Check if target exists
    if args.target not in df.columns:
        # Try to find a log-transformed version
        log_target = f"log_{args.target}"
        if log_target in df.columns:
            logger.info(f"Target '{args.target}' not found. Using '{log_target}'.")
            args.target = log_target
        else:
            logger.error(f"Target '{args.target}' (or '{log_target}') not found in data.")
            return 1

    # Calculate correlations
    logger.info(f"Calculating correlations with target '{args.target}'...")
    corr_results = calculate_correlation_pvalues(df, args.target)

    if not corr_results:
        logger.warning("No correlations calculated. Check data.")
        return 0

    # Apply BH correction
    logger.info(f"Applying Benjamini-Hochberg correction (alpha={args.alpha})...")
    corrected_df = apply_bh_correction_to_df(corr_results, args.alpha)

    # Save results
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    corrected_df.to_csv(args.output, index=False)
    logger.info(f"Saved corrected results to {args.output}")
    logger.info(f"Significant features (adjusted p < {args.alpha}): {corrected_df['is_significant'].sum()}")

    return 0

if __name__ == "__main__":
    exit(main())