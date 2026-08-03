import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.power import FTestAnovaPower

# Configure logging if not already done
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] [%(asctime)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
logger = logging.getLogger(__name__)

def log_data_gap_flag(message: str):
    logger.critical(f"[CRITICAL DATA GAP] {message}")

def log_underpowered_flag(message: str):
    logger.warning(f"[UNDERPOWERED] {message}")

def log_under_determined_flag(message: str):
    logger.warning(f"[UNDER-DETERMINED] {message}")

def calculate_vif(X: pd.DataFrame) -> pd.Series:
    """
    Calculates Variance Inflation Factor for each column in a DataFrame.
    
    This function extracts the VIF calculation logic to be reusable across
    the pipeline (e.g., in code/05_correlation.py).
    
    Args:
        X: DataFrame of predictors (no intercept column required).
    
    Returns:
        Series of VIF values indexed by column name.
    """
    # Add intercept for statsmodels
    X_with_intercept = X.copy()
    X_with_intercept['intercept'] = 1.0
    
    vif_series = pd.Series(index=X.columns, dtype=float)
    
    for col in X.columns:
        try:
            vif = variance_inflation_factor(X_with_intercept.values, list(X_with_intercept.columns).index(col))
            vif_series[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_series[col] = np.nan
    
    return vif_series

def benjamini_hochberg_fdr(p_values: List[float]) -> List[float]:
    """
    Applies Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
    
    Returns:
        List of adjusted p-values.
    """
    from statsmodels.stats.multitest import multipletests
    
    p_values = np.array(p_values)
    # Filter out NaNs for calculation, then map back? 
    # multipletests handles NaNs by returning NaN for them usually.
    rejected, pvals_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    return pvals_corrected.tolist()

def generate_checksum(file_path: str) -> str:
    """Generates a SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_permanova_power(n: int, effect_size: float = 0.15, alpha: float = 0.05) -> float:
    """
    Estimates power for PERMANOVA using F-test approximation.
    """
    power_calc = FTestAnovaPower()
    # Effect size f^2 = R^2 / (1 - R^2)
    f2 = (effect_size ** 2) / (1 - (effect_size ** 2))
    # Convert f2 to eta-squared equivalent for power calculation if needed,
    # but FTestAnovaPower expects effect_size as f (Cohen's f) or f2?
    # statsmodels FTestAnovaPower uses effect_size = f (Cohen's f).
    # f = sqrt(f2)
    f = np.sqrt(f2)
    
    try:
        power = power_calc.solve_power(effect_size=f, nobs1=n, alpha=alpha, k_groups=3) # Assuming 3 groups
        return power
    except Exception:
        return 0.0

def validate_power_requirements(power: float, n_per_group: int) -> bool:
    """Checks if power and sample size meet requirements."""
    return power >= 0.8 and n_per_group >= 10
