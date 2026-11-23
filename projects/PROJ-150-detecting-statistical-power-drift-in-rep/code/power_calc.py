import os
import sys
import logging
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_power_cohen_d(effect_size: float, sample_size: float, alpha: float = 0.05) -> float:
    """
    Calculate statistical power given Cohen's d, sample size, and alpha level.
    Assumes a two-sample t-test with equal group sizes (n1 = n2 = sample_size / 2).
    
    Args:
        effect_size: Cohen's d value.
        sample_size: Total sample size (N).
        alpha: Significance level (default 0.05).
        
    Returns:
        Statistical power (probability of rejecting null hypothesis when false).
    """
    if sample_size <= 0 or effect_size == 0:
        return 0.0
    
    n_per_group = sample_size / 2.0
    if n_per_group < 1:
        return 0.0
    
    # Non-centrality parameter for two-sample t-test
    ncp = effect_size * np.sqrt(n_per_group / 2.0)
    
    # Degrees of freedom
    df_val = int(sample_size - 2)
    
    # Critical t-value (two-tailed)
    t_crit = stats.t.ppf(1 - alpha/2, df_val)
    
    # Power calculation using non-central t-distribution
    power = 1 - stats.nct.cdf(t_crit, df_val, ncp) + stats.nct.cdf(-t_crit, df_val, ncp)
    
    return float(power)

def load_and_validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate the input DataFrame has required columns.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Validated DataFrame.
        
    Raises:
        ValueError: If required columns are missing.
    """
    required_cols = ['effect_size', 'sample_size']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df

def filter_and_log_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter rows where effect_size or sample_size are non-positive or NaN, logging warnings.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Filtered DataFrame.
    """
    mask = (df['effect_size'].isna()) | (df['sample_size'].isna()) | (df['sample_size'] <= 0)
    invalid_indices = df[mask].index.tolist()
    
    if invalid_indices:
        logger.warning(f"Filtering {len(invalid_indices)} invalid rows (NaN or non-positive sample size).")
    
    return df[~mask]

def compute_power_estimates(df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Compute power estimates for all rows in the DataFrame.
    
    Args:
        df: DataFrame with 'effect_size' and 'sample_size'.
        alpha: Significance level.
        
    Returns:
        DataFrame with added 'power_estimate' column.
    """
    df = load_and_validate_data(df)
    df = filter_and_log_invalid_rows(df)
    
    power_estimates = []
    for _, row in df.iterrows():
        power = calculate_power_cohen_d(
            row['effect_size'], 
            row['sample_size'], 
            alpha
        )
        power_estimates.append(power)
    
    df['power_estimate'] = power_estimates
    return df

def validate_output(df: pd.DataFrame) -> bool:
    """
    Validate that the output DataFrame contains no NaN in power_estimate column.
    
    Args:
        df: Output DataFrame.
        
    Returns:
        True if valid, False otherwise.
    """
    if df['power_estimate'].isna().any():
        logger.warning("Output contains NaN in power_estimate column.")
        return False
    return True

def main():
    """
    Main entry point for power calculation module (for testing).
    """
    logger.info("Power calculation module loaded.")
    # This module is primarily imported and used by preprocess.py
    # This main block is for standalone testing if needed.
    pass

if __name__ == "__main__":
    main()
