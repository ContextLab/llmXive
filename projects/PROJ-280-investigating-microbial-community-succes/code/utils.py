"""
Shared utility functions for the microbial community succession project.
Implements VIF calculation, Benjamini-Hochberg FDR, checksums, and power analysis.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import FTestAnovaPower
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Configure logging to stderr with a specific format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

def log_data_gap_flag(message: str) -> None:
    """Log a CRITICAL flag indicating a data gap."""
    logger.critical(f"[DATA GAP] {message}")

def log_underpowered_flag(message: str) -> None:
    """Log a CRITICAL flag indicating the study is underpowered."""
    logger.critical(f"[UNDERPOWERED] {message}")

def log_under_determined_flag(message: str) -> None:
    """Log a CRITICAL flag indicating the system is under-determined."""
    logger.critical(f"[UNDER-DETERMINED] {message}")

def calculate_vif(features: pd.DataFrame) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each feature in a DataFrame.
    
    Args:
        features: DataFrame where columns are predictor variables (taxa abundances).
                  Should not include the target variable.
    
    Returns:
        Series of VIF values indexed by column name.
    
    Raises:
        ValueError: If features contain non-numeric data or constant variance columns.
    """
    if features.empty:
        return pd.Series(dtype=float)
    
    # Ensure all columns are numeric
    if not np.issubdtype(features.values.dtype, np.number):
        try:
            features = features.select_dtypes(include=[np.number])
        except Exception as e:
            raise ValueError(f"Features must be numeric: {e}")
    
    # Handle constant variance columns (VIF is undefined)
    # Add a small epsilon to avoid division by zero if variance is 0
    # But first, check for zero variance columns
    zero_var_cols = features.columns[features.var() == 0]
    if len(zero_var_cols) > 0:
        logger.warning(f"Removing constant variance columns for VIF calculation: {list(zero_var_cols)}")
        features = features.drop(columns=zero_var_cols)
    
    if features.empty:
        return pd.Series(dtype=float)
    
    # Add intercept column for the regression matrix
    # VIF calculation: VIF_j = 1 / (1 - R_j^2) where R_j^2 is from regressing X_j on all other X
    # statsmodels vif function handles this internally if we pass the design matrix without intercept
    # But standard implementation:
    
    vif_data = []
    for i, col in enumerate(features.columns):
        # Create design matrix X for this iteration (all features)
        X = features.values
        # Calculate VIF for column i
        try:
            vif = variance_inflation_factor(X, i)
            vif_data.append((col, vif))
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data.append((col, np.nan))
    
    return pd.Series([v for _, v in vif_data], index=[c for c, _ in vif_data])

def benjamini_hochberg_fdr(p_values: Union[List[float], np.ndarray]) -> List[float]:
    """
    Apply Benjamini-Hochberg False Discovery Rate correction to a list of p-values.
    
    Args:
        p_values: List or array of raw p-values.
    
    Returns:
        List of adjusted p-values (q-values) in the same order as input.
    
    Note:
        Uses the standard BH procedure. If p-values are not sorted, they are
        sorted internally, corrected, and then returned in original order.
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return []
    
    # Create index array to restore original order
    indices = np.arange(n)
    
    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate BH adjusted p-values
    # q_i = p_i * n / i  (where i is rank, 1-indexed)
    # Ensure monotonicity: q_i = min(q_i, q_{i+1}, ..., q_n)
    adjusted_p = np.zeros(n)
    
    # Calculate raw BH values
    ranks = np.arange(1, n + 1)
    adjusted_p[sorted_indices] = sorted_p * n / ranks
    
    # Ensure values are <= 1
    adjusted_p = np.minimum(adjusted_p, 1.0)
    
    # Enforce monotonicity (cumulative min from the end)
    # Start from the largest rank and move backwards
    for i in range(n - 2, -1, -1):
        if adjusted_p[sorted_indices[i]] > adjusted_p[sorted_indices[i + 1]]:
            adjusted_p[sorted_indices[i]] = adjusted_p[sorted_indices[i + 1]]
    
    return adjusted_p.tolist()

def generate_checksum(file_path: Union[str, Path]) -> str:
    """
    Generate a SHA-256 checksum for a file.
    
    Args:
        file_path: Path to the file to checksum.
    
    Returns:
        Hexadecimal string of the SHA-256 hash.
    
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
    except Exception as e:
        logger.error(f"Error reading file for checksum: {e}")
        raise
    
    return sha256_hash.hexdigest()

def calculate_permanova_power(
    n_groups: int,
    n_per_group: int,
    effect_size: float = 0.15,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Estimate statistical power for PERMANOVA using F-test approximation.
    
    Args:
        n_groups: Number of groups (e.g., wetland stages).
        n_per_group: Number of samples per group.
        effect_size: Expected effect size (eta-squared or R-squared). Default 0.15 (medium).
        alpha: Significance level.
    
    Returns:
        Dictionary with power estimate and parameters.
    """
    total_n = n_groups * n_per_group
    df1 = n_groups - 1
    df2 = total_n - n_groups
    
    # Use statsmodels FTestAnovaPower
    power_calc = FTestAnovaPower()
    
    # Effect size f^2 = R^2 / (1 - R^2)
    # But FTestAnovaPower expects effect size 'f' (Cohen's f)
    # Cohen's f = sqrt(R^2 / (1 - R^2))
    try:
        f_effect = np.sqrt(effect_size / (1 - effect_size))
        power = power_calc.solve_power(
            effect_size=f_effect,
            nobs1=n_per_group,
            alpha=alpha,
            power=None,
            ratio=1.0,
            alternative='larger'
        )
    except Exception as e:
        logger.warning(f"Power calculation failed: {e}. Returning NaN.")
        power = np.nan
    
    return {
        "power": float(power) if not np.isnan(power) else None,
        "n_groups": n_groups,
        "n_per_group": n_per_group,
        "total_n": total_n,
        "effect_size_r2": effect_size,
        "alpha": alpha,
        "df1": df1,
        "df2": df2
    }

def validate_power_requirements(
    power_report: Dict[str, Any],
    min_power: float = 0.8
) -> Tuple[bool, str]:
    """
    Validate if the calculated power meets the minimum threshold.
    
    Args:
        power_report: Output from calculate_permanova_power.
        min_power: Minimum acceptable power (default 0.8).
    
    Returns:
        Tuple of (is_valid, flag_message).
    """
    power = power_report.get("power")
    if power is None:
        return False, "UNDERPOWERED (calculation failed)"
    
    if power < min_power:
        return False, f"UNDERPOWERED (power={power:.3f} < {min_power})"
    
    return True, "PASS"