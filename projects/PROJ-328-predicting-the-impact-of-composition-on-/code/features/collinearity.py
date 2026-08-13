"""
Collinearity utilities for feature engineering.
Calculates Variance Inflation Factor (VIF) and identifies collinear features.
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

logger = logging.getLogger(__name__)

def calculate_vif(X: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each feature.

    Args:
        X: DataFrame of features.

    Returns:
        Dictionary mapping feature names to VIF values.
    """
    if X.empty:
        logger.warning("Empty feature matrix provided to VIF calculation")
        return {}

    # Add constant for intercept
    X_const = sm.add_constant(X)

    vif_data = {}
    for col in X.columns:
        try:
            vif = variance_inflation_factor(X_const.values, X_const.columns.get_loc(col) + 1)
            vif_data[col] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = np.nan

    return vif_data

def get_collinear_features(vif_dict: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Identify features with VIF above the threshold.

    Args:
        vif_dict: Dictionary of VIF values.
        threshold: VIF threshold (default 5.0).

    Returns:
        List of collinear feature names.
    """
    return [col for col, vif in vif_dict.items() if not np.isnan(vif) and vif >= threshold]

def remove_collinear_features(X: pd.DataFrame, vif_dict: Dict[str, float], threshold: float = 5.0) -> pd.DataFrame:
    """
    Remove features with high VIF.

    Args:
        X: Original feature DataFrame.
        vif_dict: Dictionary of VIF values.
        threshold: VIF threshold.

    Returns:
        DataFrame with collinear features removed.
    """
    collinear = get_collinear_features(vif_dict, threshold)
    logger.info(f"Removing collinear features: {collinear}")

    remaining_cols = [col for col in X.columns if col not in collinear]
    return X[remaining_cols]

def save_vif_report(vif_dict: Dict[str, float], output_path: str):
    """
    Save VIF report to a file.

    Args:
        vif_dict: Dictionary of VIF values.
        output_path: Path to save the report.
    """
    df_vif = pd.DataFrame(list(vif_dict.items()), columns=['feature', 'vif'])
    df_vif = df_vif.sort_values('vif', ascending=False)
    df_vif.to_csv(output_path, index=False)
    logger.info(f"VIF report saved to {output_path}")

def main():
    """
    Main entry point for testing VIF calculation.
    """
    logger.info("Starting VIF calculation test")

    # Create sample data with some correlation
    np.random.seed(42)
    n = 100
    X = pd.DataFrame({
        'feature_a': np.random.randn(n),
        'feature_b': np.random.randn(n),
        'feature_c': np.random.randn(n),
        'feature_d': np.random.randn(n),
    })

    # Add correlation
    X['feature_a_corr'] = X['feature_a'] + np.random.randn(n) * 0.1

    vif_dict = calculate_vif(X)
    print("VIF Values:")
    for feat, val in sorted(vif_dict.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feat}: {val:.2f}")

    collinear = get_collinear_features(vif_dict, threshold=5.0)
    if collinear:
        print(f"\nCollinear features (VIF >= 5): {collinear}")
    else:
        print("\nNo collinear features found (VIF < 5)")

    logger.info("VIF calculation test completed")

if __name__ == "__main__":
    main()
