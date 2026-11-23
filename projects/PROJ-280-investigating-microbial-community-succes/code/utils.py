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
from statsmodels.stats.multitest import multipletests

# Global logger instance for the module
_module_logger = None

def _get_module_logger():
    """Returns the module-level logger, initializing it if necessary."""
    global _module_logger
    if _module_logger is None:
        _module_logger = logging.getLogger('utils')
    return _module_logger

def get_logger(name: str) -> logging.Logger:
    """
    Setup and return a logger with specific configuration for the project.
    
    Writes to data/processed/audit_trail.log with format:
    ^\[(INFO|WARN|ERROR|CRITICAL)\] \[\w+\] Message$
    
    Configures both FileHandler and StreamHandler; default level INFO.
    
    Args:
        name: The name for the logger (typically the module name).
    
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers if already configured (e.g. in tests or re-runs)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent double logging to root if root is configured
    
    # Ensure output directory exists
    log_dir = Path("data/processed")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / "audit_trail.log"
    
    # Define the custom format to match the required regex:
    # ^\[(INFO|WARN|ERROR|CRITICAL)\] \[\w+\] Message$
    # Note: The regex expects level in brackets, then name in brackets.
    # Standard logging levels map: INFO, WARNING (mapped to WARN in regex?), ERROR, CRITICAL.
    # The regex explicitly lists 'WARN'. We must ensure the level name is 'WARN' not 'WARNING'.
    # We use a custom formatter or filter to change WARNING to WARN.
    
    class CustomFormatter(logging.Formatter):
        def format(self, record):
            # Map WARNING to WARN to satisfy the regex requirement
            if record.levelname == 'WARNING':
                record.levelname = 'WARN'
            return super().format(record)
    
    log_format = '[%(levelname)s] [%(name)s] %(message)s'
    
    # File Handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    file_formatter = CustomFormatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    
    # Stream Handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_formatter = CustomFormatter(log_format)
    stream_handler.setFormatter(stream_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger

def log_data_gap_flag(message: str):
    logger = _get_module_logger()
    if not logger.handlers:
        logger = get_logger('utils')
    logger.critical(f"[CRITICAL DATA GAP] {message}")

def log_underpowered_flag(message: str):
    logger = _get_module_logger()
    if not logger.handlers:
        logger = get_logger('utils')
    logger.warning(f"[UNDERPOWERED] {message}")

def log_under_determined_flag(message: str):
    logger = _get_module_logger()
    if not logger.handlers:
        logger = get_logger('utils')
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
            logger = _get_module_logger()
            if logger:
                logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_series[col] = np.nan
    
    return vif_series

def fdr_correction(p_values: np.ndarray) -> np.ndarray:
    """
    Applies Benjamini-Hochberg FDR correction to an array of p-values.
    
    Args:
        p_values: numpy array of raw p-values.
    
    Returns:
        numpy array of adjusted p-values.
    """
    # multipletests returns (reject, pvals_corrected, alphacSID, alphacBH)
    # We only need the corrected p-values.
    _, pvals_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    return pvals_corrected

def compute_file_hash(file_path: str) -> str:
    """
    Computes the SHA-256 hex digest of a file.
    
    Args:
        file_path: Path to the file to hash.
    
    Returns:
        Hexadecimal string of the SHA-256 hash.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_checksum(file_path: str) -> str:
    """Generates a SHA256 checksum for a file (alias for compute_file_hash)."""
    return compute_file_hash(file_path)

def estimate_power(n_per_group: int, effect_size: float) -> float:
    """
    Estimates statistical power for an ANOVA F-test.
    
    Uses statsmodels FTestAnovaPower to solve for power given sample size per group
    and effect size (Cohen's f).
    
    Args:
        n_per_group: Number of samples per group.
        effect_size: Cohen's f effect size.
    
    Returns:
        Estimated power (float between 0 and 1). Returns 0.0 if calculation fails.
    """
    power_calc = FTestAnovaPower()
    # k_groups is assumed to be 3 (Early, Intermediate, Mature) based on project context
    k_groups = 3
    alpha = 0.05
    
    try:
        # solve_power can solve for any of: effect_size, nobs1, alpha, power, k_groups
        # We solve for 'power'
        power = power_calc.solve_power(
            effect_size=effect_size,
            nobs1=n_per_group,
            alpha=alpha,
            k_groups=k_groups,
            alternative='two-sided'
        )
        return float(power)
    except Exception as e:
        logger = _get_module_logger()
        if logger:
            logger.warning(f"Power calculation failed: {e}")
        return 0.0

def calculate_permanova_power(n: int, effect_size: float = 0.15, alpha: float = 0.05) -> float:
    """
    Estimates power for PERMANOVA using F-test approximation.
    
    Args:
        n: Total number of samples (or n_per_group depending on interpretation, 
           here treated as nobs1 per group for consistency with ANOVA).
        effect_size: Target R-squared effect size.
        alpha: Significance level.
    
    Returns:
        Estimated power.
    """
    power_calc = FTestAnovaPower()
    # Effect size f^2 = R^2 / (1 - R^2)
    f2 = (effect_size ** 2) / (1 - (effect_size ** 2))
    # statsmodels FTestAnovaPower uses effect_size as f (Cohen's f).
    f = np.sqrt(f2)
    
    try:
        # Assuming 3 groups (Early, Intermediate, Mature)
        power = power_calc.solve_power(effect_size=f, nobs1=n, alpha=alpha, k_groups=3)
        return power
    except Exception:
        return 0.0

def validate_power_requirements(power: float, n_per_group: int) -> bool:
    """Checks if power and sample size meet requirements."""
    return power >= 0.8 and n_per_group >= 10