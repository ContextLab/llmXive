import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Union

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log_data_gap_flag(message: str) -> None:
    """Log a CRITICAL DATA GAP flag."""
    logger.critical(f"CRITICAL DATA GAP: {message}")

def log_underpowered_flag(message: str) -> None:
    """Log an UNDERPOWERED flag."""
    logger.critical(f"UNDERPOWERED: {message}")

def log_under_determined_flag(message: str) -> None:
    """Log an UNDER-DETERMINED flag."""
    logger.critical(f"UNDER-DETERMINED: {message}")

def calculate_vif(X: pd.DataFrame) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor in DataFrame X.
    """
    if X.shape[0] <= X.shape[1]:
        logger.warning("Sample size <= number of features. VIF calculation may be unstable.")
    
    vif_data = pd.Series(index=X.columns, dtype=float)
    for i, col in enumerate(X.columns):
        # Regress col against all other columns
        y = X[col]
        X_other = X.drop(columns=[col])
        
        # Handle potential singular matrix issues
        try:
            r_squared = stats.linregress(X_other.values, y.values)[2]**2 if X_other.shape[1] == 1 else stats.linregress(X_other.values.flatten(), y.values)[2]**2 # Simplified for 1D
            # Proper OLS for multiple regression
            from sklearn.linear_model import LinearRegression
            model = LinearRegression()
            model.fit(X_other, y)
            r_squared = model.score(X_other, y)
            
            vif = 1 / (1 - r_squared)
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = np.nan
    
    return vif_data

def benjamini_hochberg_fdr(p_values: Union[List[float], np.ndarray]) -> np.ndarray:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Parameters:
    p_values (list or array): List of p-values.
    
    Returns:
    np.ndarray: Array of adjusted p-values.
    """
    if len(p_values) == 0:
        return np.array([])
    
    # Use statsmodels implementation which is robust
    # method='fdr_bh' implements Benjamini-Hochberg
    _, adjusted_p, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    return adjusted_p

def generate_checksum(file_path: str) -> str:
    """
    Generate SHA-256 checksum for a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_permanova_power(n_samples: int, effect_size: float = 0.15) -> Dict[str, Any]:
    """
    Estimate statistical power for PERMANOVA.
    """
    from statsmodels.stats.power import FTestAnovaPower
    f_effect = np.sqrt(effect_size**2 / (1 - effect_size**2))
    alpha = 0.05
    k = 2 # Assume 2 groups
    n_per_group = n_samples // k
    
    power_analysis = FTestAnovaPower()
    if n_per_group > 0:
        power = power_analysis.solve_power(effect_size=f_effect, nobs1=n_per_group, alpha=alpha, ratio=1.0, alternative='larger')
    else:
        power = 0.0
        
    return {
        "power": float(power),
        "n_per_group": n_per_group,
        "effect_size": effect_size,
        "flag": "UNDERPOWERED" if power < 0.8 or n_per_group < 10 else "PASS"
    }

def validate_power_requirements(power_report: Dict[str, Any]) -> bool:
    """
    Validate power requirements.
    """
    if power_report['flag'] == "UNDERPOWERED":
        log_underpowered_flag(f"Power analysis failed: Power={power_report['power']:.2f}, n_per_group={power_report['n_per_group']}")
        return False
    return True
