import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import logging
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence

logger = logging.getLogger(__name__)

def run_ols_regression(data: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, Any]:
    """
    Perform OLS regression on log-transformed data.
    
    Args:
        data: DataFrame containing the data
        x_col: Column name for independent variable
        y_col: Column name for dependent variable
        
    Returns:
        Dictionary with regression results (exponent, ci_low, ci_high, p_value)
    """
    if data.empty or len(data) < 2:
        logger.warning("Insufficient data for regression")
        return {
            'exponent': np.nan,
            'ci_low': np.nan,
            'ci_high': np.nan,
            'p_value': np.nan,
            'r_squared': np.nan
        }
    
    # Log-transform
    x = np.log(data[x_col].dropna())
    y = np.log(data[y_col].dropna())
    
    if len(x) != len(y) or len(x) < 2:
        logger.warning("Mismatched or insufficient log-transformed data")
        return {
            'exponent': np.nan,
            'ci_low': np.nan,
            'ci_high': np.nan,
            'p_value': np.nan,
            'r_squared': np.nan
        }
    
    # Add constant for intercept
    X = sm.add_constant(x)
    model = sm.OLS(y, X)
    results = model.fit()
    
    # Get confidence intervals for slope (index 1)
    conf_int = results.conf_int(alpha=0.05)
    
    return {
        'exponent': results.params[1],
        'ci_low': conf_int.iloc[1, 0],
        'ci_high': conf_int.iloc[1, 1],
        'p_value': results.pvalues[1],
        'r_squared': results.rsquared
    }

def calculate_correlation_matrix(data: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    Calculate correlation matrix for specified columns.
    
    Args:
        data: DataFrame containing the data
        cols: List of column names to include
        
    Returns:
        Correlation matrix as DataFrame
    """
    valid_cols = [c for c in cols if c in data.columns]
    if len(valid_cols) < 2:
        logger.warning("Insufficient columns for correlation matrix")
        return pd.DataFrame()
    
    return data[valid_cols].corr()

def detect_percolation_threshold(data: pd.DataFrame, connectivity_col: str = 'percolation_flag', 
                                 degree_col: str = 'avg_degree', threshold: float = 0.8) -> Optional[float]:
    """
    Detect percolation threshold as the smallest average degree where >= threshold fraction is connected.
    
    Args:
        data: DataFrame with simulation results
        connectivity_col: Column name indicating connectivity (1=connected, 0=disconnected)
        degree_col: Column name for average degree
        threshold: Minimum fraction of connected graphs (default 0.8)
        
    Returns:
        Percolation threshold value (smallest avg_degree meeting criterion) or None
    """
    if data.empty:
        logger.warning("Empty data for percolation threshold detection")
        return None
    
    # Sort by average degree
    sorted_data = data.sort_values(by=degree_col)
    
    # Calculate cumulative connectivity fraction for each degree level
    percolation_threshold = None
    
    # Group by degree and calculate connectivity fraction
    degree_groups = sorted_data.groupby(degree_col)[connectivity_col].mean()
    
    for degree, connected_frac in degree_groups.items():
        if connected_frac >= threshold:
            percolation_threshold = degree
            logger.info(f"Percolation threshold detected at avg_degree={degree} (connectivity={connected_frac:.2f})")
            break
    
    if percolation_threshold is None:
        logger.warning(f"No percolation threshold found with connectivity >= {threshold}")
        
    return percolation_threshold

def update_csv_with_percolation_threshold(csv_path: str, output_path: Optional[str] = None) -> bool:
    """
    Calculate percolation threshold from simulation results and add it as a column.
    
    Args:
        csv_path: Path to input CSV file
        output_path: Path for output CSV (defaults to same as input if None)
        
    Returns:
        True if successful, False otherwise
    """
    if output_path is None:
        output_path = csv_path
    
    try:
        df = pd.read_csv(csv_path)
        
        if 'percolation_flag' not in df.columns or 'avg_degree' not in df.columns:
            logger.error("Required columns 'percolation_flag' or 'avg_degree' not found in CSV")
            return False
        
        # Calculate percolation threshold
        threshold_value = detect_percolation_threshold(df)
        
        if threshold_value is None:
            logger.warning("Could not determine percolation threshold")
            # Add column with NaN
            df['percolation_threshold'] = np.nan
        else:
            # Add the threshold value to all rows
            df['percolation_threshold'] = threshold_value
            logger.info(f"Added percolation_threshold={threshold_value} to all rows")
        
        # Write to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Updated CSV written to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating CSV with percolation threshold: {e}")
        return False

def analyze_scaling_law(data: pd.DataFrame, x_col: str = 'avg_degree', 
                        y_col: str = 'conductivity') -> Dict[str, Any]:
    """
    Analyze scaling law between topology metric and conductivity.
    
    Args:
        data: DataFrame with simulation results
        x_col: Column name for topology metric (default: avg_degree)
        y_col: Column name for conductivity (default: conductivity)
        
    Returns:
        Dictionary with scaling analysis results
    """
    if data.empty:
        return {'scaling_exponent': np.nan, 'is_significant': False, 'message': 'Empty data'}
    
    # Run regression
    reg_results = run_ols_regression(data, x_col, y_col)
    
    # Check significance
    is_significant = reg_results['p_value'] < 0.05 if not np.isnan(reg_results['p_value']) else False
    
    result = {
        'scaling_exponent': reg_results['exponent'],
        'ci_low': reg_results['ci_low'],
        'ci_high': reg_results['ci_high'],
        'p_value': reg_results['p_value'],
        'r_squared': reg_results['r_squared'],
        'is_significant': is_significant,
        'message': f"Scaling exponent: {reg_results['exponent']:.4f}" + 
                  (f" (p={reg_results['p_value']:.4f}, significant)" if is_significant 
                   else f" (p={reg_results['p_value']:.4f}, not significant)")
    }
    
    return result
