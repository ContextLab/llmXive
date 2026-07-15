import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import logging
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence

def run_ols_regression(df: pd.DataFrame, x_col: str, y_col: str) -> Optional[Dict[str, Any]]:
    """Run OLS regression on log-transformed data."""
    try:
        # Filter out zero or negative values for log transform
        mask = (df[x_col] > 0) & (df[y_col] > 0)
        if mask.sum() < 2:
            logging.warning("Not enough valid data points for regression")
            return None
        
        df_valid = df[mask].copy()
        X = np.log(df_valid[x_col].values)
        y = np.log(df_valid[y_col].values)
        
        # Add constant for intercept
        X_with_const = sm.add_constant(X)
        
        model = sm.OLS(y, X_with_const)
        results = model.fit()
        
        # Extract key metrics
        exponent = results.params[1]  # slope
        p_value = results.pvalues[1]
        r_squared = results.rsquared
        
        # Confidence interval (95%)
        ci = results.conf_int(alpha=0.05)
        ci_lower = ci.iloc[1, 0]
        ci_upper = ci.iloc[1, 1]
        
        # Percolation threshold detection
        percolation_threshold = detect_percolation_threshold(df_valid)
        
        return {
            'exponent': exponent,
            'p_value': p_value,
            'r_squared': r_squared,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'percolation_threshold': percolation_threshold
        }
    except Exception as e:
        logging.error(f"Regression failed: {e}")
        return None

def calculate_correlation_matrix(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Calculate correlation matrix for specified columns."""
    return df[cols].corr()

def detect_percolation_threshold(df: pd.DataFrame) -> float:
    """Detect percolation threshold: smallest avg_degree where >=80% connected."""
    if 'percolation_flag' not in df.columns or 'avg_degree' not in df.columns:
        logging.warning("Missing required columns for percolation detection")
        return 0.0
    
    # Sort by avg_degree
    df_sorted = df.sort_values('avg_degree')
    
    # Find first point where percolation_flag >= 0.8 (80%)
    # Since percolation_flag is binary (0 or 1), we look for first 1
    percolated = df_sorted[df_sorted['percolation_flag'] == 1]
    
    if len(percolated) == 0:
        return 0.0
    
    # Return the smallest avg_degree where percolation is achieved
    return percolated['avg_degree'].min()

def update_csv_with_percolation_threshold(csv_path: str, threshold: float):
    """Update CSV file with percolation threshold value."""
    try:
        df = pd.read_csv(csv_path)
        # Add or update percolation_threshold column
        df['percolation_threshold'] = threshold
        df.to_csv(csv_path, index=False)
        logging.info(f"Updated CSV with percolation threshold: {threshold}")
    except Exception as e:
        logging.error(f"Failed to update CSV with percolation threshold: {e}")

def analyze_scaling_law(df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, Any]:
    """Analyze scaling law between topology metric and conductivity."""
    reg_result = run_ols_regression(df, x_col, y_col)
    if not reg_result:
        return {}
    
    # Check statistical significance
    if reg_result['p_value'] < 0.05:
        significance = "statistically significant"
    else:
        significance = "not statistically significant"
    
    return {
        'exponent': reg_result['exponent'],
        'significance': significance,
        'p_value': reg_result['p_value'],
        'r_squared': reg_result['r_squared'],
        'percolation_threshold': reg_result['percolation_threshold']
    }
