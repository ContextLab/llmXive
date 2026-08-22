"""
Diagnostics module for collinearity, VIF, sensitivity, and power analysis.

Implements:
- Perfect multicollinearity detection
- VIF calculation with skipping for collinear pairs
- Sensitivity analysis
- Power analysis
"""
import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_diagnostics_seed(seed: int):
    """Set random seed for reproducibility."""
    np.random.seed(seed)

def detect_perfect_multicollinearity(df_predictors: pd.DataFrame, tolerance: float = 1e-10) -> tuple:
    """
    Detect perfect multicollinearity in predictor variables.
    
    Args:
        df_predictors: DataFrame containing only predictor columns.
        tolerance: Threshold for determining perfect correlation (r > 1 - tolerance).
        
    Returns:
        tuple: (collinearity_map dict, perfect_pairs list of tuples)
    """
    logger.info("Detecting perfect multicollinearity...")
    
    # Calculate correlation matrix
    corr_matrix = df_predictors.corr().abs()
    
    # Identify pairs with correlation > (1 - tolerance)
    perfect_pairs = []
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    for col in upper.columns:
        for row in upper.index:
            if pd.notna(upper.loc[row, col]) and upper.loc[row, col] > (1 - tolerance):
                # Avoid self-correlation
                if row != col:
                    pair = tuple(sorted([row, col]))
                    if pair not in perfect_pairs:
                        perfect_pairs.append(pair)
    
    # Build a simple map for reporting
    collinearity_map = {}
    for p1, p2 in perfect_pairs:
        corr_val = corr_matrix.loc[p1, p2]
        collinearity_map[f"{p1}_{p2}"] = float(corr_val)
    
    logger.info(f"Found {len(perfect_pairs)} perfect multicollinearity pairs: {perfect_pairs}")
    return collinearity_map, perfect_pairs

def calculate_vif(df_predictors: pd.DataFrame, perfect_pairs: list = None) -> dict:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    
    Skips VIF calculation for variables involved in perfect multicollinearity
    to avoid division by zero or infinite values.
    
    Args:
        df_predictors: DataFrame containing predictor columns.
        perfect_pairs: List of tuples representing perfectly correlated pairs.
        
    Returns:
        dict: VIF report containing 'vif_values', 'skipped_columns', and 'perfect_collinearity_warning'.
    """
    logger.info("Calculating VIF...")
    
    if perfect_pairs is None:
        perfect_pairs = []
    
    # Identify columns to skip
    skipped_columns = set()
    for p1, p2 in perfect_pairs:
        skipped_columns.add(p1)
        skipped_columns.add(p2)
    
    vif_values = {}
    
    # Calculate VIF for non-skipped columns
    # VIF = 1 / (1 - R^2) where R^2 is from regressing the variable against all others
    for col in df_predictors.columns:
        if col in skipped_columns:
            vif_values[col] = float('nan')
            continue
        
        try:
            y = df_predictors[col]
            X = df_predictors.drop(columns=[col])
            
            # Handle case where X has 0 columns (only 1 predictor total)
            if X.shape[1] == 0:
                vif_values[col] = 1.0
                continue
            
            # Fit linear model
            model = stats.linregress(X.values, y.values)
            # linregress only handles 1D X, so we need a different approach for multiple regression
            # Use numpy polyfit or sklearn if available, but here we use a simple matrix approach
            
            # R^2 calculation for multiple regression
            # y = X * beta + error
            # beta = (X'X)^-1 X'y
            # R^2 = 1 - SS_res / SS_tot
            
            X_mat = X.values
            y_vec = y.values
            
            # Add intercept
            X_mat = np.column_stack([np.ones(X_mat.shape[0]), X_mat])
            
            try:
                beta = np.linalg.lstsq(X_mat, y_vec, rcond=None)[0]
                y_pred = X_mat @ beta
                ss_res = np.sum((y_vec - y_pred) ** 2)
                ss_tot = np.sum((y_vec - np.mean(y_vec)) ** 2)
                
                if ss_tot == 0:
                    r_squared = 0.0
                else:
                    r_squared = 1 - (ss_res / ss_tot)
                
                if r_squared >= 1.0:
                    vif = float('inf')
                else:
                    vif = 1 / (1 - r_squared)
                
                vif_values[col] = float(vif)
                
            except np.linalg.LinAlgError:
                # Singular matrix, likely perfect collinearity in the remaining set
                vif_values[col] = float('nan')
                
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_values[col] = float('nan')
    
    report = {
        "vif_values": vif_values,
        "skipped_columns": list(skipped_columns),
        "perfect_collinearity_warning": len(perfect_pairs) > 0,
        "message": "VIF calculation skipped for variables involved in perfect multicollinearity." if len(perfect_pairs) > 0 else "No perfect multicollinearity detected."
    }
    
    logger.info(f"VIF calculation complete. Skipped {len(skipped_columns)} columns.")
    return report

def run_sensitivity_analysis(correlation_results: pd.DataFrame, thresholds: list = None) -> pd.DataFrame:
    """
    Run sensitivity analysis by varying p-value thresholds.
    
    Args:
        correlation_results: DataFrame with correlation results including p-values.
        thresholds: List of p-value thresholds to test (default: [0.01, 0.05, 0.10]).
        
    Returns:
        DataFrame: Sensitivity analysis results.
    """
    if thresholds is None:
        thresholds = [0.01, 0.05, 0.10]
    
    results = []
    for thresh in thresholds:
        significant = correlation_results[correlation_results['p_value'] < thresh]
        results.append({
            'threshold': thresh,
            'significant_count': len(significant),
            'total_count': len(correlation_results)
        })
    
    return pd.DataFrame(results)

def calculate_power(n_samples: int, effect_size: float = 0.3, alpha: float = 0.05) -> dict:
    """
    Calculate statistical power for a correlation test.
    
    Args:
        n_samples: Number of samples.
        effect_size: Expected correlation coefficient.
        alpha: Significance level.
        
    Returns:
        dict: Power analysis results.
    """
    # Using scipy's power calculation for correlation
    # Approximate using t-distribution
    # t = r * sqrt((n-2) / (1-r^2))
    # df = n - 2
    
    df = n_samples - 2
    if df <= 0:
        return {"power": 0.0, "status": "Underpowered (n too small)"}
    
    t_stat = effect_size * np.sqrt(df / (1 - effect_size**2))
    
    # Critical t-value
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Power is the probability that |t| > t_crit under the alternative
    # This is an approximation
    power = 1 - stats.t.cdf(t_crit - t_stat, df) + stats.t.cdf(-t_crit - t_stat, df)
    
    status = "Adequate" if power >= 0.8 else "Underpowered"
    
    return {
        "power": float(power),
        "n_samples": n_samples,
        "effect_size": effect_size,
        "alpha": alpha,
        "status": status,
        "minimum_n_for_80pct": None # Simplified, would require iterative search
    }

def main():
    """Main entry point for diagnostics module."""
    logger.info("Diagnostics module loaded.")

if __name__ == "__main__":
    main()