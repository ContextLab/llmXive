import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import logging
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence

logger = logging.getLogger(__name__)

def run_ols_regression(x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Perform OLS regression on log-transformed data.
    
    Args:
        x: Independent variable (e.g., log(avg_degree))
        y: Dependent variable (e.g., log(conductivity))
        
    Returns:
        Dictionary containing regression results:
        - slope: Scaling exponent
        - intercept: Log-conductivity intercept
        - p_value: p-value for the slope
        - r_squared: R-squared value
        - conf_int: 95% confidence interval for slope
    """
    if len(x) < 3:
        logger.warning("Insufficient data points for regression (< 3).")
        return {
            "slope": np.nan,
            "intercept": np.nan,
            "p_value": np.nan,
            "r_squared": np.nan,
            "conf_int": (np.nan, np.nan)
        }
    
    # Add constant for intercept
    X = sm.add_constant(x)
    model = sm.OLS(y, X).fit()
    
    slope = model.params[1]
    intercept = model.params[0]
    p_value = model.pvalues[1]
    r_squared = model.rsquared
    conf_int = model.conf_int(alpha=0.05).iloc[1].tolist()
    
    return {
        "slope": slope,
        "intercept": intercept,
        "p_value": p_value,
        "r_squared": r_squared,
        "conf_int": conf_int
    }

def calculate_correlation_matrix(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    Calculate correlation matrix for specified columns.
    
    Args:
        df: DataFrame containing the data
        cols: List of column names to include
        
    Returns:
        Correlation matrix as DataFrame
    """
    if not all(col in df.columns for col in cols):
        missing = set(cols) - set(df.columns)
        raise ValueError(f"Missing columns in DataFrame: {missing}")
    
    return df[cols].corr()

def detect_percolation_threshold(df: pd.DataFrame, connectivity_col: str = 'percolation_flag') -> float:
    """
    Detect the percolation threshold: smallest average degree where >= 80% of networks are connected.
    
    Args:
        df: DataFrame with simulation results
        connectivity_col: Name of column indicating connectivity (1=connected, 0=disconnected)
        
    Returns:
        The percolation threshold value (average degree)
    """
    if connectivity_col not in df.columns:
        raise ValueError(f"Column '{connectivity_col}' not found in DataFrame")
    
    # Group by average degree and calculate connectivity rate
    grouped = df.groupby('avg_degree')[connectivity_col].mean().reset_index()
    grouped.columns = ['avg_degree', 'connectivity_rate']
    
    # Find the smallest avg_degree where connectivity_rate >= 0.80
    threshold_rows = grouped[grouped['connectivity_rate'] >= 0.80]
    
    if threshold_rows.empty:
        logger.warning("No percolation threshold found (connectivity never reached 80%).")
        return np.nan
    
    threshold = threshold_rows['avg_degree'].min()
    logger.info(f"Percolation threshold detected at avg_degree = {threshold:.4f}")
    return threshold

def update_csv_with_percolation_threshold(csv_path: str, threshold: float) -> None:
    """
    Update the CSV file by adding a 'percolation_threshold' column with the detected value.
    
    Args:
        csv_path: Path to the simulation results CSV
        threshold: The detected percolation threshold value
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # Add the threshold as a constant column for all rows (or just first row if preferred)
    # Based on T027a description: "storage of the percolation threshold value into ... as a new column"
    df['percolation_threshold'] = threshold
    
    df.to_csv(csv_path, index=False)
    logger.info(f"Updated {csv_path} with percolation_threshold = {threshold}")

def analyze_scaling_law(
    df: pd.DataFrame,
    x_col: str = 'avg_degree',
    y_col: str = 'conductivity',
    percolation_threshold: Optional[float] = None
) -> Dict[str, Any]:
    """
    Analyze the scaling law between topology (avg_degree) and conductivity.
    
    Conditionally reports the scaling exponent only if:
    1. The mean degree of the dataset exceeds the percolation_threshold (if provided)
    2. The p-value of the slope is < 0.05
    
    Args:
        df: DataFrame with simulation results
        x_col: Column name for independent variable (avg_degree)
        y_col: Column name for dependent variable (conductivity)
        percolation_threshold: Optional threshold to filter data or condition reporting
        
    Returns:
        Dictionary with analysis results including conditional reporting flags.
    """
    # Filter out NaNs
    valid_data = df[[x_col, y_col]].dropna()
    
    if len(valid_data) < 3:
        logger.warning("Insufficient valid data points for scaling analysis.")
        return {
            "slope": np.nan,
            "p_value": np.nan,
            "r_squared": np.nan,
            "is_significant": False,
            "reporting_condition_met": False,
            "message": "Insufficient data"
        }
    
    # Log-transform for power-law fitting: log(y) = slope * log(x) + intercept
    x_log = np.log(valid_data[x_col].values)
    y_log = np.log(valid_data[y_col].values)
    
    results = run_ols_regression(x_log, y_log)
    
    mean_degree = valid_data[x_col].mean()
    reporting_condition_met = True
    message_parts = []
    
    # Check percolation threshold condition if provided
    if percolation_threshold is not None and not np.isnan(percolation_threshold):
        if mean_degree <= percolation_threshold:
            reporting_condition_met = False
            message_parts.append(f"Mean degree ({mean_degree:.2f}) is below percolation threshold ({percolation_threshold:.2f}).")
        else:
            message_parts.append(f"Mean degree ({mean_degree:.2f}) exceeds percolation threshold ({percolation_threshold:.2f}).")
    else:
        message_parts.append("No percolation threshold provided for filtering.")
    
    # Check statistical significance
    is_significant = results['p_value'] < 0.05
    
    if is_significant:
        message_parts.append(f"Scaling exponent is statistically significant (p={results['p_value']:.4f} < 0.05).")
    else:
        message_parts.append(f"Scaling exponent is NOT statistically significant (p={results['p_value']:.4f} >= 0.05).")
    
    if not reporting_condition_met or not is_significant:
        logger.warning("Conditional reporting requirements not met. Exponent not reported as significant.")
    
    return {
        "slope": results['slope'],
        "intercept": results['intercept'],
        "p_value": results['p_value'],
        "r_squared": results['r_squared'],
        "conf_int": results['conf_int'],
        "mean_degree": mean_degree,
        "percolation_threshold": percolation_threshold,
        "is_significant": is_significant,
        "reporting_condition_met": reporting_condition_met,
        "message": " ".join(message_parts)
    }