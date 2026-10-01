import os
import sys
import logging
import traceback
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import pearsonr

from config import get_config, require_data_dir, Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def power_law(N: float, a: float, b: float) -> float:
    """
    Power-law model: Error = a * N^(-b)
    
    Args:
        N: Dataset size (sample count)
        a: Intercept coefficient
        b: Scaling exponent
    
    Returns:
        Predicted error
    """
    if N <= 0:
        return float('inf')
    return a * (N ** -b)

def fit_power_law(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Fit a power-law model to learning curve data.
    
    Uses non-linear least squares fitting.
    Falls back to linear regression on log-log transformed data if non-linear fails.
    
    Args:
        x: Array of dataset sizes (N)
        y: Array of error values
    
    Returns:
        Tuple of (a, b, r_squared, fit_status)
        fit_status is 'success' or 'non-power-law'
    """
    if len(x) < 2:
        logger.warning("Insufficient data points for power-law fitting.")
        return np.nan, np.nan, np.nan, 'insufficient_data'
    
    # Filter out non-positive N or infinite errors
    mask = (x > 0) & np.isfinite(y)
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        logger.warning("Cleaned data has insufficient points.")
        return np.nan, np.nan, np.nan, 'insufficient_data'
    
    # Try non-linear fitting first
    try:
        # Initial guess: a=1.0, b=0.5
        p0 = [1.0, 0.5]
        bounds = ([0, 0], [np.inf, 2.0])  # a > 0, 0 < b < 2
        
        popt, pcov = curve_fit(
            lambda N, a, b: a * (N ** -b),
            x_clean,
            y_clean,
            p0=p0,
            bounds=bounds,
            maxfev=5000
        )
        
        a, b = popt
        y_pred = power_law(x_clean, a, b)
        
        # Calculate R-squared
        ss_res = np.sum((y_clean - y_pred) ** 2)
        ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        status = 'success' if r_squared >= 0.9 else 'non-power-law'
        logger.info(f"Non-linear fit: a={a:.4f}, b={b:.4f}, R²={r_squared:.4f}, Status={status}")
        return a, b, r_squared, status

    except Exception as e:
        logger.warning(f"Non-linear fit failed: {e}. Falling back to log-log linear regression.")
        
        # Fallback: Log-log linear regression
        # log(Error) = log(a) - b * log(N)
        # y' = A - b * x'  where y' = log(y), x' = log(x), A = log(a)
        
        log_x = np.log(x_clean)
        log_y = np.log(y_clean)
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = np.polyfit(log_x, log_y, 1, full=False)
        
        b = -slope  # Because model is N^(-b)
        a = np.exp(intercept)
        
        r_squared = r_value ** 2
        
        status = 'success' if r_squared >= 0.9 else 'non-power-law'
        logger.info(f"Log-log fit: a={a:.4f}, b={b:.4f}, R²={r_squared:.4f}, Status={status}")
        return a, b, r_squared, status

def load_learning_curve_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load learning curve data from CSV.
    
    Args:
        input_path: Path to the learning curves CSV file.
                   If None, uses default path from config.
    
    Returns:
        DataFrame with learning curve data.
    
    Raises:
        FileNotFoundError: If file not found.
    """
    config = get_config()
    
    if input_path is None:
        # Default path relative to project root
        data_dir = require_data_dir(config)
        input_path = str(data_dir / 'learning_curves.csv')
    else:
        input_path = str(Path(input_path))
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Learning curve file not found: {input_path}")
    
    logger.info(f"Loading learning curves from: {input_path}")
    df = pd.read_csv(input_path)
    
    required_cols = ['property_name', 'subset_size', 'error']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in learning curves file: {missing}")
    
    return df

def process_property_scaling(
    df: pd.DataFrame,
    property_name: str,
    min_subset_size: int = 1000,
    max_subset_size: int = 40000
) -> Optional[Dict[str, Any]]:
    """
    Fit scaling law for a single property.
    
    Args:
        df: Full learning curves DataFrame
        property_name: Name of the property to process
        min_subset_size: Minimum subset size to consider
        max_subset_size: Maximum subset size to consider
    
    Returns:
        Dictionary with scaling results or None if data insufficient.
    """
    # Filter data for this property
    prop_data = df[df['property_name'] == property_name]
    
    if prop_data.empty:
        logger.warning(f"No data for property: {property_name}")
        return None
    
    # Filter by subset size range
    prop_data = prop_data[
        (prop_data['subset_size'] >= min_subset_size) &
        (prop_data['subset_size'] <= max_subset_size)
    ]
    
    if prop_data.empty:
        logger.warning(f"No valid subset sizes for property: {property_name}")
        return None
    
    # Sort by subset size
    prop_data = prop_data.sort_values('subset_size')
    
    x = prop_data['subset_size'].values
    y = prop_data['error'].values
    
    # Fit power law
    a, b, r_squared, status = fit_power_law(x, y)
    
    return {
        'property_name': property_name,
        'exponent_b': b,
        'intercept_a': a,
        'r_squared': r_squared,
        'fit_status': status,
        'num_points': len(x)
    }

def main(input_path: Optional[str] = None, output_path: Optional[str] = None):
    """
    Main entry point for fitting scaling laws.
    
    Reads learning curves, fits power-law models per property,
    and outputs results to CSV.
    
    Args:
        input_path: Path to learning curves CSV.
        output_path: Path to output scaling results CSV.
    """
    logger.info("Starting scaling law fitting process")
    
    config = get_config()
    
    # Load data
    try:
        df = load_learning_curve_data(input_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} learning curve records")
    
    # Get unique properties
    properties = df['property_name'].unique()
    logger.info(f"Found {len(properties)} properties: {list(properties)}")
    
    results = []
    
    for prop in properties:
        logger.info(f"Processing property: {prop}")
        result = process_property_scaling(df, prop)
        if result:
            results.append(result)
    
    if not results:
        logger.error("No scaling results generated. Check input data.")
        sys.exit(1)
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Ensure correct column order
    columns = ['property_name', 'exponent_b', 'intercept_a', 'r_squared', 'fit_status']
    results_df = results_df[columns]
    
    # Determine output path
    if output_path is None:
        data_dir = require_data_dir(config)
        output_path = str(data_dir / 'scaling_results.csv')
    else:
        output_path = str(Path(output_path))
    
    # Save results
    logger.info(f"Saving scaling results to: {output_path}")
    results_df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully processed {len(results)} properties")
    logger.info(f"Output saved to: {output_path}")
    
    # Print summary
    logger.info("Summary:")
    logger.info(results_df.to_string(index=False))
    
    # Check for non-power-law properties
    non_pl = results_df[results_df['fit_status'] == 'non-power-law']
    if len(non_pl) > 0:
        logger.warning(f"{len(non_pl)} properties classified as non-power-law")
    
    return results_df

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fit scaling laws to learning curve data")
    parser.add_argument('--input', type=str, default=None, help='Input learning curves CSV')
    parser.add_argument('--output', type=str, default=None, help='Output scaling results CSV')
    
    args = parser.parse_args()
    
    main(args.input, args.output)