import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import logging
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence

logger = logging.getLogger(__name__)

def run_ols_regression(df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, Any]:
    """
    Perform OLS regression on log-transformed data.
    Returns a dictionary with exponent, confidence interval, and p-value.
    """
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        logger.error("Invalid data for regression.")
        return {}

    # Drop rows with NaN in relevant columns
    data = df[[x_col, y_col]].dropna()
    if len(data) < 2:
        logger.warning("Insufficient data points for regression.")
        return {}

    X = np.log(data[x_col].values)
    y = np.log(data[y_col].values)

    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()

    if len(model.params) < 2:
        logger.error("Regression failed to converge properly.")
        return {}

    exponent = model.params[1]
    p_value = model.pvalues[1]
    conf_int = model.conf_int().iloc[1].tolist()

    return {
        "exponent": exponent,
        "p_value": p_value,
        "confidence_interval": conf_int,
        "r_squared": model.rsquared
    }

def calculate_correlation_matrix(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    Calculate correlation matrix for specified columns.
    """
    if df.empty:
        logger.warning("Empty dataframe for correlation matrix.")
        return pd.DataFrame()

    valid_cols = [c for c in cols if c in df.columns]
    if len(valid_cols) < 2:
        logger.warning("Not enough valid columns for correlation.")
        return pd.DataFrame()

    return df[valid_cols].corr()

def detect_percolation_threshold(results: List[Dict[str, Any]], threshold_pct: float = 0.8) -> Optional[float]:
    """
    Detect the percolation threshold: the smallest average degree where
    at least `threshold_pct` (default 80%) of simulations are connected.

    Args:
        results: List of simulation result dictionaries containing 'avg_degree' and 'percolation_flag'.
        threshold_pct: The connectivity fraction threshold (e.g., 0.8 for 80%).

    Returns:
        The smallest average degree meeting the criteria, or None if not found.
    """
    if not results:
        logger.warning("No results provided for percolation threshold detection.")
        return None

    # Group by avg_degree to calculate connectivity rate per degree level
    # We need to aggregate results by avg_degree
    df = pd.DataFrame(results)
    if 'avg_degree' not in df.columns or 'percolation_flag' not in df.columns:
        logger.error("Missing required columns 'avg_degree' or 'percolation_flag' in results.")
        return None

    # Calculate connectivity rate per avg_degree
    connectivity_stats = df.groupby('avg_degree')['percolation_flag'].mean().reset_index()
    connectivity_stats.columns = ['avg_degree', 'connectivity_rate']

    # Filter for degrees where connectivity rate >= threshold
    valid_degrees = connectivity_stats[connectivity_stats['connectivity_rate'] >= threshold_pct]['avg_degree']

    if valid_degrees.empty:
        logger.info(f"No average degree found with connectivity >= {threshold_pct*100:.0f}%")
        return None

    # Return the smallest average degree meeting the criteria
    threshold_value = valid_degrees.min()
    logger.info(f"Percolation threshold detected at avg_degree = {threshold_value:.4f} "
                f"(connectivity rate >= {threshold_pct*100:.0f}%)")
    return threshold_value

def analyze_scaling_law(df: pd.DataFrame, x_col: str = 'avg_degree', y_col: str = 'conductivity') -> Dict[str, Any]:
    """
    Full analysis of scaling law between topology metric and conductivity.
    Includes regression and percolation threshold detection.
    """
    if df.empty:
        logger.warning("Empty dataframe for scaling law analysis.")
        return {}

    regression_results = run_ols_regression(df, x_col, y_col)
    
    # Detect percolation threshold
    # We need to pass the raw data (list of dicts) to detect_percolation_threshold
    # or convert df to list of dicts if needed. 
    # Assuming df contains the full simulation results including percolation_flag
    percolation_threshold = None
    if 'percolation_flag' in df.columns:
        percolation_threshold = detect_percolation_threshold(df.to_dict('records'))

    return {
        "regression": regression_results,
        "percolation_threshold": percolation_threshold
    }
