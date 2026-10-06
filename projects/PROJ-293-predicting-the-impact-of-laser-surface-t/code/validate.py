"""
Statistical validation and power analysis for LST wear resistance study.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import f
from scipy.special import bdtr, bdtrc

# Setup logging
from logging_config import setup_logging, get_logger
logger = get_logger(__name__)

# Constants
DEFAULT_ALPHA = 0.05
DEFAULT_MIN_POWER = 0.8
DEFAULT_EXPECTED_F2 = 0.15  # Medium effect size

def calculate_effect_size_f2(predictors: int, r_squared: float) -> float:
    """
    Calculate Cohen's f^2 effect size from R-squared.
    
    f^2 = R^2 / (1 - R^2)
    
    Args:
        predictors: Number of predictor variables (not used in calculation but kept for API)
        r_squared: R-squared value from model fit
        
    Returns:
        f^2 effect size
        
    Raises:
        ValueError: If r_squared is 1.0 (perfect fit) or negative
    """
    if r_squared >= 1.0:
        raise ValueError("R-squared must be less than 1.0 for valid effect size calculation")
    if r_squared < 0:
        raise ValueError("R-squared cannot be negative")
    
    return r_squared / (1 - r_squared)

def calculate_power_regression(sample_size: int, predictors: int, f2: float, alpha: float = DEFAULT_ALPHA) -> float:
    """
    Calculate statistical power for multiple regression using the non-central F-distribution.
    
    This uses the approximation based on the non-centrality parameter λ = f^2 * N
    where N is the sample size.
    
    Args:
        sample_size: Number of observations (N)
        predictors: Number of predictor variables (k)
        f2: Cohen's f^2 effect size
        alpha: Significance level (default 0.05)
        
    Returns:
        Statistical power (probability of rejecting null hypothesis when false)
    """
    if sample_size <= predictors:
        logger.warning(f"Sample size ({sample_size}) <= predictors ({predictors}). Power = 0.0")
        return 0.0
    
    if f2 <= 0:
        logger.warning(f"Effect size f^2 ({f2}) must be positive. Power = 0.0")
        return 0.0
    
    # Degrees of freedom
    df1 = predictors  # numerator df
    df2 = sample_size - predictors - 1  # denominator df
    
    if df2 <= 0:
        logger.warning(f"Insufficient degrees of freedom. Power = 0.0")
        return 0.0
    
    # Non-centrality parameter: λ = f^2 * N
    ncp = f2 * sample_size
    
    # Critical F value
    f_crit = f.ppf(1 - alpha, df1, df2)
    
    # Power = P(F > f_crit | H1) where F follows non-central F distribution
    # Using the relationship: Power = 1 - CDF of non-central F at f_crit
    # We approximate using the non-central beta distribution
    # Power = 1 - I_{df1*f_crit/(df1*f_crit + df2)}(df1/2, df2/2, λ)
    
    # Alternative: Use the non-central F CDF directly if available
    # scipy.stats.ncf is available in newer versions
    try:
        from scipy.stats import ncf
        power = 1 - ncf.cdf(f_crit, df1, df2, ncp)
    except ImportError:
        # Fallback approximation using normal approximation to non-central F
        # This is less accurate but works without ncf
        mu_ncf = df2 * (df1 + ncp) / (df1 * (df2 - 2)) if df2 > 2 else 1.0
        sigma_ncf = np.sqrt(2 * df2**2 * (df1 + ncp)**2 + 4 * df2 * (df1 + ncp) * df1) / (df1 * (df2 - 2) * np.sqrt(df1)) if df2 > 2 else 1.0
        
        z = (f_crit - mu_ncf) / sigma_ncf if sigma_ncf > 0 else 0
        from scipy.stats import norm
        power = 1 - norm.cdf(z)
    
    return max(0.0, min(1.0, power))

def estimate_predictors_from_data(df: pd.DataFrame, target_col: str) -> int:
    """
    Estimate the number of predictors in a DataFrame after encoding.
    
    For categorical variables, counts the number of dummy variables created.
    For continuous variables, counts as 1.
    
    Args:
        df: DataFrame containing features and target
        target_col: Name of the target column
        
    Returns:
        Estimated number of predictors
    """
    predictors = 0
    features = [col for col in df.columns if col != target_col]
    
    for col in features:
        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
            # Categorical: count unique values minus 1 (reference category)
            n_unique = df[col].nunique()
            predictors += max(0, n_unique - 1)
        else:
            # Continuous/numeric: count as 1
            predictors += 1
    
    return predictors

def run_power_analysis(data_path: str, output_path: str, 
                      min_power_threshold: float = DEFAULT_MIN_POWER,
                      alpha: float = DEFAULT_ALPHA,
                      expected_f2: float = DEFAULT_EXPECTED_F2) -> Dict[str, Any]:
    """
    Execute statistical power analysis for the regression study.
    
    Reads the normalized dataset, estimates predictors, calculates power,
    and writes results to the output JSON file.
    
    Args:
        data_path: Path to the normalized dataset CSV
        output_path: Path to write the power analysis results JSON
        min_power_threshold: Minimum acceptable power (default 0.8)
        alpha: Significance level (default 0.05)
        expected_f2: Expected effect size (default 0.15, medium)
        
    Returns:
        Dictionary with power analysis results
        
    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data is invalid
    """
    logger.info(f"Running power analysis on {data_path}")
    
    # Load data
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} records from {data_path}")
    
    # Estimate predictors
    target_col = 'wear_rate'  # Standard target for this study
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data")
    
    n_predictors = estimate_predictors_from_data(df, target_col)
    sample_size = len(df)
    
    logger.info(f"Sample size: {sample_size}, Predictors: {n_predictors}")
    
    # Calculate power
    power = calculate_power_regression(
        sample_size=sample_size,
        predictors=n_predictors,
        f2=expected_f2,
        alpha=alpha
    )
    
    logger.info(f"Calculated power: {power:.4f} (threshold: {min_power_threshold})")
    
    # Determine status
    status = 'passed' if power >= min_power_threshold else 'failed'
    reason = None if status == 'passed' else 'insufficient_power'
    
    # Prepare result
    result = {
        'status': status,
        'power': float(power),
        'sample_size': int(sample_size),
        'n_predictors': int(n_predictors),
        'alpha': alpha,
        'expected_f2': expected_f2,
        'min_power_threshold': min_power_threshold,
        'reason': reason,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Power analysis results written to {output_path}")
    
    # Exit with appropriate code if called as main
    if status == 'failed':
        logger.error(f"Power analysis failed: {reason}")
        sys.exit(1)
    
    return result

def main():
    """
    Main entry point for power analysis script.
    Reads configuration from environment or defaults.
    """
    setup_logging()
    
    # Default paths
    data_path = os.environ.get('POWER_DATA_PATH', 'data/processed/normalized_only.csv')
    output_path = os.environ.get('POWER_OUTPUT_PATH', 'reports/power_analysis.json')
    
    # Get parameters from environment or use defaults
    min_power = float(os.environ.get('POWER_MIN_THRESHOLD', DEFAULT_MIN_POWER))
    alpha = float(os.environ.get('POWER_ALPHA', DEFAULT_ALPHA))
    expected_f2 = float(os.environ.get('POWER_EXPECTED_F2', DEFAULT_EXPECTED_F2))
    
    try:
        run_power_analysis(
            data_path=data_path,
            output_path=output_path,
            min_power_threshold=min_power,
            alpha=alpha,
            expected_f2=expected_f2
        )
        logger.info("Power analysis completed successfully")
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
