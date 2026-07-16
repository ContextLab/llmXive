import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import logging
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence
import csv
import os

logger = logging.getLogger(__name__)

def run_ols_regression(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Run OLS regression on log-transformed conductivity vs average degree.
    
    Returns dict with exponent, CI, p-value, or None if insufficient data.
    """
    if not os.path.exists(filepath):
        logger.error(f"File {filepath} not found")
        return None
    
    df = pd.read_csv(filepath)
    
    # Filter for connected graphs (percolation_flag == 1)
    connected_df = df[df['percolation_flag'] == 1]
    
    if len(connected_df) < 2:
        logger.warning("Insufficient connected data points for regression")
        return None
    
    X = connected_df['avg_degree'].values
    y = connected_df['conductivity'].values
    
    # Log transform
    # Avoid log(0)
    valid_mask = (X > 0) & (y > 0)
    if np.sum(valid_mask) < 2:
        logger.warning("No valid positive data for log transformation")
        return None
    
    X_log = np.log(X[valid_mask])
    y_log = np.log(y[valid_mask])
    
    # Add constant for intercept
    X_log_const = sm.add_constant(X_log)
    
    model = sm.OLS(y_log, X_log_const)
    results = model.fit()
    
    # Extract exponent (slope)
    exponent = results.params[1]
    p_value = results.pvalues[1]
    
    # Confidence interval (95%)
    ci = results.conf_int(alpha=0.05)
    ci_slope = ci.iloc[1].tolist()
    
    logger.info(f"Regression: exponent={exponent:.4f}, p={p_value:.4f}, CI={ci_slope}")
    
    return {
        'exponent': exponent,
        'p_value': p_value,
        'ci_lower': ci_slope[0],
        'ci_upper': ci_slope[1],
        'r_squared': results.rsquared
    }

def calculate_correlation_matrix(filepath: str) -> Optional[pd.DataFrame]:
    """Calculate correlation matrix for all metrics."""
    if not os.path.exists(filepath):
        return None
    
    df = pd.read_csv(filepath)
    numeric_cols = ['avg_degree', 'conductivity', 'p', 'N']
    # Only include columns that exist
    existing_cols = [c for c in numeric_cols if c in df.columns]
    
    if len(existing_cols) < 2:
        return None
    
    corr = df[existing_cols].corr()
    logger.info("Correlation matrix calculated")
    return corr

def detect_percolation_threshold(filepath: str) -> Optional[float]:
    """
    Detect percolation threshold: smallest avg degree where >= 80% connected.
    """
    if not os.path.exists(filepath):
        return None
    
    df = pd.read_csv(filepath)
    
    # Group by avg_degree (binned if necessary, but assume exact values for now)
    # Calculate connectivity rate per degree
    degree_stats = df.groupby('avg_degree').agg(
        connected=('percolation_flag', 'mean')
    ).reset_index()
    
    # Find degrees where connected >= 0.8
    threshold_candidates = degree_stats[degree_stats['connected'] >= 0.8]
    
    if threshold_candidates.empty:
        logger.warning("No percolation threshold found (no degree with >= 80% connectivity)")
        return None
    
    # Smallest avg degree meeting criteria
    threshold = threshold_candidates['avg_degree'].min()
    logger.info(f"Percolation threshold detected at avg_degree={threshold:.2f}")
    return threshold

def update_csv_with_percolation_threshold(filepath: str, threshold: float) -> None:
    """
    Update the CSV file to include percolation_threshold column.
    This function adds a column where every row has the threshold value 
    (as a global property of the dataset) or marks rows relative to it.
    Per T027a, we store the value.
    """
    if not os.path.exists(filepath):
        return
    
    # Read
    df = pd.read_csv(filepath)
    
    # Add column
    df['percolation_threshold'] = threshold
    
    # Write back
    df.to_csv(filepath, index=False)
    logger.info(f"Updated {filepath} with percolation_threshold={threshold}")

def analyze_scaling_law(filepath: str) -> Dict[str, Any]:
    """
    Full analysis: regression + percolation threshold.
    Integrates results into the CSV as required by T029.
    """
    results = {}
    
    # 1. Detect threshold
    threshold = detect_percolation_threshold(filepath)
    if threshold is not None:
        update_csv_with_percolation_threshold(filepath, threshold)
        results['percolation_threshold'] = threshold
    
    # 2. Run regression
    reg_results = run_ols_regression(filepath)
    if reg_results:
        results.update(reg_results)
        
        # 3. Conditional reporting (T028):
        # Report if p < 0.05 AND mean degree > threshold
        if reg_results['p_value'] < 0.05 and threshold is not None:
            # Calculate mean degree of connected data
            df = pd.read_csv(filepath)
            connected_df = df[df['percolation_flag'] == 1]
            mean_deg = connected_df['avg_degree'].mean()
            
            if mean_deg > threshold:
                logger.info(f"Statistically significant scaling (p={reg_results['p_value']:.3f}) above threshold {threshold:.2f}")
                results['significant_above_threshold'] = True
            else:
                results['significant_above_threshold'] = False
    
    return results

# For T029 integration: This module is now called from main.py to ensure
# regression results are computed and the CSV is updated with percolation_threshold.
# The actual "appending" of regression metadata to the CSV is handled by 
# update_csv_with_percolation_threshold which adds the column.
# If specific regression coefficients need to be appended per-row, that would 
# require a different schema, but the spec implies a global threshold column.
