import os
import json
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy import stats
from code.config import DATA_PATH, TARGET_VAR
from code.logging_config import setup_logging

logger = setup_logging()

def calculate_correlation_pvalues(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = None
) -> pd.DataFrame:
    """
    Calculate Pearson correlation coefficients and p-values between each feature
    and the target variable.

    Args:
        df: DataFrame containing features and target
        feature_cols: List of feature column names
        target_col: Name of the target column. If None, uses config TARGET_VAR.

    Returns:
        DataFrame with columns: feature, correlation, p_value
    """
    if target_col is None:
        target_col = TARGET_VAR

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame. "
                         f"Available columns: {list(df.columns)}")

    results = []
    target_data = df[target_col].dropna()

    for feature in feature_cols:
        if feature not in df.columns:
            logger.warning(f"Feature '{feature}' not found in DataFrame, skipping.")
            continue

        feature_data = df[feature].dropna()

        # Align indices to handle missing values consistently
        common_idx = target_data.index.intersection(feature_data.index)
        if len(common_idx) < 10:
            logger.warning(f"Not enough data points for feature '{feature}' "
                           f"({len(common_idx)}), skipping.")
            continue

        x = feature_data.loc[common_idx]
        y = target_data.loc[common_idx]

        # Calculate Pearson correlation and p-value
        corr, p_value = stats.pearsonr(x, y)
        results.append({
            'feature': feature,
            'correlation': corr,
            'p_value': p_value
        })

    return pd.DataFrame(results)

def main():
    """
    Main entry point to calculate feature-conductivity correlations.
    Reads processed descriptors, computes correlations with target,
    and saves results to data/processed/correlation_results.csv.
    """
    logger.info("Starting correlation analysis...")

    # Load processed descriptors
    descriptors_path = os.path.join(DATA_PATH, 'processed', 'descriptors.csv')
    if not os.path.exists(descriptors_path):
        raise FileNotFoundError(f"Descriptors file not found: {descriptors_path}")

    df = pd.read_csv(descriptors_path)
    logger.info(f"Loaded {len(df)} molecules from {descriptors_path}")

    # Determine target variable
    target_var = TARGET_VAR
    if target_var not in df.columns:
        # Fallback to HOMO_LUMO_gap if conductivity missing
        if 'HOMO_LUMO_gap' in df.columns:
            logger.warning(f"Target '{target_var}' not found. Using 'HOMO_LUMO_gap' instead.")
            target_var = 'HOMO_LUMO_gap'
        else:
            raise ValueError("Neither conductivity nor HOMO_LUMO_gap found in data.")

    # Define feature columns (exclude non-feature columns)
    exclude_cols = ['smiles', 'status', target_var]
    feature_cols = [col for col in df.columns if col not in exclude_cols]

    if not feature_cols:
        raise ValueError("No feature columns found in descriptors file.")

    logger.info(f"Calculating correlations for {len(feature_cols)} features against '{target_var}'")

    # Calculate correlations
    corr_results = calculate_correlation_pvalues(df, feature_cols, target_var)

    # Sort by absolute correlation value
    corr_results['abs_correlation'] = corr_results['correlation'].abs()
    corr_results = corr_results.sort_values('abs_correlation', ascending=False)

    # Save results
    output_path = os.path.join(DATA_PATH, 'processed', 'correlation_results.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    corr_results[['feature', 'correlation', 'p_value']].to_csv(output_path, index=False)

    logger.info(f"Correlation results saved to {output_path}")
    logger.info(f"Top 5 features by absolute correlation:\n{corr_results.head(5)}")

    return corr_results

if __name__ == "__main__":
    main()