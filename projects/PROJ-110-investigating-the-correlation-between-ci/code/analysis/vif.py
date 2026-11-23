"""
Utility functions for calculating Variance Inflation Factor (VIF) to assess multicollinearity.
"""

import logging
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate VIF for each column in the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing only numeric predictor columns.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['feature', 'VIF'].
    """
    # Ensure no missing values
    if df.isnull().any().any():
        raise ValueError("Input DataFrame contains NaN values; cannot compute VIF.")
    # Convert to numpy array
    X = df.values
    vif_data = []
    for i in range(X.shape[1]):
        vif = variance_inflation_factor(X, i)
        vif_data.append(vif)
    result = pd.DataFrame({"feature": df.columns, "VIF": vif_data})
    return result

def flag_high_vif(vif_df: pd.DataFrame, threshold: float = 5.0) -> list:
    """
    Return a list of feature names whose VIF exceeds the given threshold.

    Parameters
    ----------
    vif_df : pd.DataFrame
        DataFrame produced by ``calculate_vif`` with columns ['feature', 'VIF'].
    threshold : float, default 5.0
        VIF threshold above which a feature is considered problematic.

    Returns
    -------
    list
        List of feature names with VIF > threshold.
    """
    high = vif_df[vif_df["VIF"] > threshold]["feature"].tolist()
    if high:
        logger.warning("High VIF detected for features: %s", high)
    return high
