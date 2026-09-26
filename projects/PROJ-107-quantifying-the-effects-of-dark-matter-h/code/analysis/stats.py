import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from scipy import stats as scipy_stats
import pandas as pd
import logging
import os
from pathlib import Path
from utils.config import get_project_root, get_data_processed_path

logger = logging.getLogger(__name__)

def apply_bonferroni_correction(p_values: List[float], n_tests: int) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        n_tests: Total number of tests performed.
        
    Returns:
        List of corrected p-values.
    """
    if not p_values:
        return []
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected

def kruskal_wallis_test(group_data: Dict[str, np.ndarray]) -> Tuple[float, float]:
    """
    Perform Kruskal-Wallis H-test for independent samples.
    
    Args:
        group_data: Dictionary mapping group names to arrays of values.
        
    Returns:
        Tuple of (H-statistic, p-value).
    """
    if len(group_data) < 2:
        raise ValueError("At least two groups are required for Kruskal-Wallis test.")
    
    samples = [data for data in group_data.values()]
    h_stat, p_val = scipy_stats.kruskal(*samples)
    return h_stat, p_val

def mann_whitney_u_test(group1: np.ndarray, group2: np.ndarray, alternative='two-sided') -> Tuple[float, float]:
    """
    Perform Mann-Whitney U test.
    
    Args:
        group1: Array of values for group 1.
        group2: Array of values for group 2.
        alternative: Hypothesis alternative ('two-sided', 'less', 'greater').
        
    Returns:
        Tuple of (U-statistic, p-value).
    """
    u_stat, p_val = scipy_stats.mannwhitneyu(group1, group2, alternative=alternative)
    return u_stat, p_val

def ks_test(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float]:
    """
    Perform Kolmogorov-Smirnov two-sample test.
    
    Args:
        group1: Array of values for group 1.
        group2: Array of values for group 2.
        
    Returns:
        Tuple of (D-statistic, p-value).
    """
    d_stat, p_val = scipy_stats.ks_2samp(group1, group2)
    return d_stat, p_val

def nearest_neighbor_matching(
    treatment_group: pd.DataFrame,
    control_group: pd.DataFrame,
    match_col: str,
    tolerance: float = 0.1
) -> pd.DataFrame:
    """
    Perform nearest neighbor matching on a specific column (e.g., halo mass).
    
    Args:
        treatment_group: DataFrame of the treatment group.
        control_group: DataFrame of the control group.
        match_col: Column name to match on.
        tolerance: Maximum allowed difference in match_col for a valid match.
        
    Returns:
        DataFrame containing matched pairs (or the treatment group with a match indicator).
    """
    # Sort by matching column to facilitate nearest neighbor search
    treatment_sorted = treatment_group.sort_values(by=match_col).reset_index(drop=True)
    control_sorted = control_group.sort_values(by=match_col).reset_index(drop=True)
    
    matched_indices = []
    used_control_indices = set()
    
    control_vals = control_sorted[match_col].values
    
    for idx, row in treatment_sorted.iterrows():
        t_val = row[match_col]
        # Calculate distances to all available control points
        distances = np.abs(control_vals - t_val)
        
        # Find the closest unused control point
        valid_mask = np.array([i not in used_control_indices for i in range(len(control_vals))])
        if not np.any(valid_mask):
            break
            
        valid_distances = distances[valid_mask]
        valid_indices = np.where(valid_mask)[0]
        
        min_idx_in_valid = np.argmin(valid_distances)
        best_control_idx = valid_indices[min_idx_in_valid]
        
        if valid_distances[min_idx_in_valid] <= tolerance:
            matched_indices.append(best_control_idx)
            used_control_indices.add(best_control_idx)
        else:
            matched_indices.append(None) # No valid match found within tolerance
    
    treatment_sorted['matched_control_idx'] = matched_indices
    return treatment_sorted

def linear_regression_with_mass_control(
    df: pd.DataFrame,
    shape_col: str,
    property_col: str,
    mass_col: str = 'halo_mass'
) -> Dict[str, Any]:
    """
    Perform linear regression of a galaxy property on a shape parameter,
    controlling for halo mass.
    
    Specifically designed to handle 'triaxiality' and 'b_a_ratio' columns
    from data/processed/halo_shapes.csv as requested in T023.
    
    Args:
        df: DataFrame containing the data (merged halo/galaxy properties).
        shape_col: Name of the shape column (e.g., 'triaxiality', 'b_a_ratio').
        property_col: Name of the galaxy property column (e.g., 'SFR', 'radius').
        mass_col: Name of the mass column to control for.
        
    Returns:
        Dictionary containing regression results:
        - coefficients: dict mapping feature names to coefficients
        - p_values: dict mapping feature names to p-values
        - r_squared: float
        - f_statistic: float
        - f_p_value: float
    """
    # Validate columns exist
    required_cols = [shape_col, property_col, mass_col]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for regression: {missing}")
    
    # Drop rows with NaN in relevant columns
    clean_df = df[[shape_col, property_col, mass_col]].dropna()
    
    if len(clean_df) < 3:
        logger.warning(f"Not enough data points for regression after cleaning (n={len(clean_df)}).")
        return {
            'coefficients': {},
            'p_values': {},
            'r_squared': np.nan,
            'f_statistic': np.nan,
            'f_p_value': np.nan,
            'n_samples': len(clean_df),
            'error': 'Insufficient data'
        }
    
    X = clean_df[[shape_col, mass_col]].values
    y = clean_df[property_col].values
    
    # Add intercept
    X_with_intercept = np.column_stack((np.ones(len(X)), X))
    
    # Solve OLS: beta = (X'X)^-1 X'y
    try:
        beta = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
    except np.linalg.LinAlgError:
        logger.error("Singular matrix in regression. Cannot compute coefficients.")
        return {
            'coefficients': {},
            'p_values': {},
            'r_squared': np.nan,
            'f_statistic': np.nan,
            'f_p_value': np.nan,
            'n_samples': len(clean_df),
            'error': 'Singular matrix'
        }
    
    # Calculate residuals
    y_pred = X_with_intercept @ beta
    residuals = y - y_pred
    
    # Calculate R-squared
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    # Calculate standard errors and p-values
    n = len(y)
    p = X_with_intercept.shape[1] - 1 # number of predictors
    
    mse = ss_res / (n - p - 1)
    try:
        var_beta = mse * np.linalg.inv(X_with_intercept.T @ X_with_intercept)
    except np.linalg.LinAlgError:
        logger.error("Cannot invert X'X for standard errors.")
        var_beta = np.full((p+1, p+1), np.nan)
        
    se_beta = np.sqrt(np.diag(var_beta))
    
    t_stats = beta / se_beta
    # Two-tailed p-values for t-distribution
    p_values = 2 * (1 - scipy_stats.t.cdf(np.abs(t_stats), df=n - p - 1))
    
    # F-statistic
    if ss_tot != 0:
        f_stat = (r_squared / p) / ((1 - r_squared) / (n - p - 1))
        f_p_value = 1 - scipy_stats.f.cdf(f_stat, p, n - p - 1)
    else:
        f_stat = np.nan
        f_p_value = np.nan
    
    feature_names = ['intercept', shape_col, mass_col]
    
    results = {
        'coefficients': {name: float(val) for name, val in zip(feature_names, beta)},
        'p_values': {name: float(val) for name, val in zip(feature_names, p_values)},
        'r_squared': float(r_squared),
        'f_statistic': float(f_stat) if not np.isnan(f_stat) else float('nan'),
        'f_p_value': float(f_p_value) if not np.isnan(f_p_value) else float('nan'),
        'n_samples': int(n),
        'shape_variable': shape_col,
        'property_variable': property_col,
        'control_variable': mass_col
    }
    
    logger.info(f"Regression completed: {property_col} ~ {shape_col} + {mass_col} (n={n}, R2={r_squared:.4f})")
    
    return results

def main():
    """
    Entry point for testing the stats module directly.
    """
    logger.info("Running stats module main...")
    # Example usage would go here if run as a script
    pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()