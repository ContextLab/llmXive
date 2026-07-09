"""
Feature engineering and diagnostic utilities for the regret and deferral study.

This module implements:
1. Min-Max Regret proxy calculation (opportunity cost).
2. Standard Deviation of Normalized EU (legacy/comparison).
3. Potential Loss Magnitude (Loss Aversion control).
4. Diagnostic correlation analysis between Regret and Loss Aversion metrics.
"""
import logging
import warnings
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

def calculate_min_max_regret(options: List[Dict[str, Any]]) -> float:
    """
    Calculate the 'Min-Max Regret' proxy (opportunity cost) for a set of options.
    
    Regret is defined as the difference between the maximum possible utility 
    (best option in the set) and the utility of the chosen option.
    For a deferral (no choice), the regret is the difference between the 
    best option and the null option (assumed 0 utility unless specified).
    
    Args:
        options: List of dictionaries representing decision options.
                 Each dict must contain at least 'utility' (or 'normalized_eu').
                 If 'chosen' is True, it indicates the selected option.
                 
    Returns:
        float: The regret value. 0 if only one option or if no options provided.
    """
    if not options or len(options) == 0:
        logger.warning("Empty options list provided to calculate_min_max_regret")
        return 0.0
    
    if len(options) == 1:
        # Per FR-002: Regret is 0 when only one option exists
        return 0.0
    
    # Extract utilities
    utilities = []
    chosen_idx = -1
    
    for i, opt in enumerate(options):
        # Try 'normalized_eu' first, fallback to 'utility'
        u = opt.get('normalized_eu') or opt.get('utility')
        if u is None:
            raise ValueError(f"Option {i} missing 'normalized_eu' or 'utility'")
        utilities.append(float(u))
        
        if opt.get('chosen', False):
            chosen_idx = i
    
    utilities = np.array(utilities)
    max_utility = np.max(utilities)
    
    if chosen_idx == -1:
        # Deferral case: No option chosen. 
        # Regret is max_utility - utility_of_null_option.
        # Assuming null option utility is 0 (neutral state).
        # If the data provides a 'deferral_utility', use that.
        null_utility = 0.0
        return float(max_utility - null_utility)
    else:
        chosen_utility = utilities[chosen_idx]
        return float(max_utility - chosen_utility)

def calculate_sd_normalized_eu(options: List[Dict[str, Any]]) -> float:
    """
    Calculate the Standard Deviation of Normalized EU (SD of EU).
    
    This is the legacy proxy mentioned in the original spec (FR-002) which 
    was replaced by Min-Max Regret due to circularity concerns. 
    Kept here for sensitivity analysis and comparison purposes.
    
    Args:
        options: List of option dictionaries with 'normalized_eu'.
                 
    Returns:
        float: Standard deviation of the utilities.
    """
    if not options or len(options) < 2:
        return 0.0
    
    utilities = [float(opt.get('normalized_eu') or opt.get('utility', 0)) 
                 for opt in options]
    return float(np.std(utilities, ddof=1))

def calculate_potential_loss_magnitude(options: List[Dict[str, Any]]) -> float:
    """
    Calculate the 'Potential Loss Magnitude' metric.
    
    This metric represents the maximum possible loss in the choice set,
    independent of the choice made. It serves as a control for loss aversion.
    Defined as: max(utility) - min(utility) in the set.
    
    Args:
        options: List of option dictionaries with 'normalized_eu'.
                 
    Returns:
        float: The range of utilities (max - min).
    """
    if not options or len(options) < 2:
        return 0.0
    
    utilities = [float(opt.get('normalized_eu') or opt.get('utility', 0)) 
                 for opt in options]
    return float(max(utilities) - min(utilities))

def add_regret_and_loss_metrics(df: pd.DataFrame, options_col: str = 'options') -> pd.DataFrame:
    """
    Add 'regret_proxy' and 'potential_loss_magnitude' columns to a DataFrame.
    
    Args:
        df: Input DataFrame containing the options column.
        options_col: Name of the column containing the list of options.
        
    Returns:
        DataFrame with added columns.
    """
    df = df.copy()
    
    def compute_row_metrics(row):
        opts = row[options_col]
        if not isinstance(opts, list):
            logger.warning(f"Non-list options found in row. Returning 0s.")
            return pd.Series({'regret_proxy': 0.0, 'potential_loss_magnitude': 0.0})
        
        regret = calculate_min_max_regret(opts)
        loss_mag = calculate_potential_loss_magnitude(opts)
        return pd.Series({'regret_proxy': regret, 'potential_loss_magnitude': loss_mag})
    
    result = df.apply(compute_row_metrics, axis=1)
    df['regret_proxy'] = result['regret_proxy']
    df['potential_loss_magnitude'] = result['potential_loss_magnitude']
    
    return df

def compute_regret_loss_correlation(df: pd.DataFrame, 
                                    regret_col: str = 'regret_proxy',
                                    loss_col: str = 'potential_loss_magnitude') -> Dict[str, Any]:
    """
    Diagnostic function to compare the correlation between regret_proxy and 
    potential_loss_magnitude.
    
    This addresses the Kahneman review concern about isolating anticipated regret
    from general loss aversion. A high correlation suggests the metrics are 
    confounded; a lower correlation suggests they capture distinct constructs.
    
    Args:
        df: DataFrame containing the metrics.
        regret_col: Name of the regret proxy column.
        loss_col: Name of the potential loss magnitude column.
        
    Returns:
        Dictionary containing:
            - correlation: Pearson correlation coefficient
            - p_value: p-value for the correlation test
            - n_samples: Number of samples used
            - interpretation: Qualitative assessment of the correlation strength
    """
    if regret_col not in df.columns or loss_col not in df.columns:
        raise ValueError(f"Columns '{regret_col}' and/or '{loss_col}' not found in DataFrame")
    
    # Drop rows where either metric is NaN or infinite
    valid_data = df[[regret_col, loss_col]].dropna()
    valid_data = valid_data[np.isfinite(valid_data[regret_col]) & np.isfinite(valid_data[loss_col])]
    
    if len(valid_data) < 2:
        logger.warning("Insufficient data points to compute correlation (n < 2)")
        return {
            'correlation': np.nan,
            'p_value': np.nan,
            'n_samples': len(valid_data),
            'interpretation': 'Insufficient data',
            'success': False
        }
    
    x = valid_data[regret_col].values
    y = valid_data[loss_col].values
    
    corr, p_val = stats.pearsonr(x, y)
    
    # Interpretation logic
    abs_corr = abs(corr)
    if abs_corr < 0.1:
        interp = "Negligible correlation. Metrics appear distinct."
    elif abs_corr < 0.3:
        interp = "Weak correlation. Metrics are largely distinct."
    elif abs_corr < 0.5:
        interp = "Moderate correlation. Some overlap between constructs."
    elif abs_corr < 0.7:
        interp = "Strong correlation. Significant overlap; consider orthogonalization."
    else:
        interp = "Very strong correlation. Metrics may be confounded."
    
    logger.info(f"Regret vs Loss Aversion Correlation: r={corr:.4f}, p={p_val:.4f} ({interp})")
    
    return {
        'correlation': float(corr),
        'p_value': float(p_val),
        'n_samples': len(valid_data),
        'interpretation': interp,
        'success': True
    }