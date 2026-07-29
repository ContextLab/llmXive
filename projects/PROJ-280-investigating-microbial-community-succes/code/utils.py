import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
from scipy.stats import f
from statsmodels.stats.power import FTestAnovaPower

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/pipeline.log')
    ]
)
logger = logging.getLogger('utils')

def log_data_gap_flag(message: str) -> None:
    """Log a CRITICAL DATA GAP flag."""
    logger.critical(f"CRITICAL DATA GAP: {message}")

def log_underpowered_flag(message: str) -> None:
    """Log an UNDERPOWERED flag."""
    logger.critical(f"UNDERPOWERED: {message}")

def log_under_determined_flag(message: str) -> None:
    """Log an UNDER-DETERMINED flag."""
    logger.critical(f"UNDER-DETERMINED: {message}")

def calculate_vif(data: np.ndarray) -> np.ndarray:
    """
    Calculate Variance Inflation Factor for each feature.
    data: array-like, shape (n_samples, n_features)
    Returns: array of VIF values
    """
    if len(data.shape) == 1:
        data = data.reshape(-1, 1)
    
    n_features = data.shape[1]
    vif = np.zeros(n_features)
    
    for i in range(n_features):
        # Regress feature i against all other features
        y = data[:, i]
        X = np.delete(data, i, axis=1)
        # Add intercept
        X = np.column_stack([np.ones(X.shape[0]), X])
        
        # OLS
        try:
            # beta = (X'X)^-1 X'y
            XtX = X.T @ X
            XtX_inv = np.linalg.inv(XtX)
            beta = XtX_inv @ X.T @ y
            y_pred = X @ beta
            residuals = y - y_pred
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2 = 1 - (ss_res / ss_tot)
            vif[i] = 1 / (1 - r2) if r2 < 1 else np.inf
        except np.linalg.LinAlgError:
            vif[i] = np.inf
    
    return vif

def benjamini_hochberg_fdr(p_values: list) -> list:
    """
    Apply Benjamini-Hochberg FDR correction.
    p_values: list of p-values
    Returns: list of adjusted p-values
    """
    from statsmodels.stats.multitest import multipletests
    _, p_adjusted, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    return p_adjusted.tolist()

def generate_checksum(file_path: Path) -> str:
    """Generate SHA-256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_permanova_power(n_samples: int, n_groups: int, effect_size: float = 0.15) -> float:
    """
    Estimate power for PERMANOVA using F-test approximation.
    effect_size (f2) = R^2 / (1 - R^2)
    """
    f2 = effect_size / (1 - effect_size)
    power_analysis = FTestAnovaPower()
    try:
        power = power_analysis.solve_power(effect_size=np.sqrt(f2),
                                           nobs=n_samples,
                                           alpha=0.05,
                                           power=None,
                                           ratio=1.0,
                                           alternative='larger')
        return float(power) if not np.isnan(power) else 0.0
    except Exception:
        return 0.0

def validate_power_requirements(power: float, n_per_group: int, min_power: float = 0.8, min_n: int = 10) -> bool:
    """
    Validate power requirements.
    Returns True if power >= min_power AND n_per_group >= min_n
    """
    return (power >= min_power) and (n_per_group >= min_n)
