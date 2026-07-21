"""
Shared utility functions for the microbial community succession pipeline.
Includes VIF calculation, FDR correction, checksums, and power analysis.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import FTestAnovaPower

# Configure logging for this module
logger = logging.getLogger(__name__)


def log_data_gap_flag(message: str, output_dir: Optional[Path] = None) -> None:
    """
    Log a critical data gap flag and optionally write to a log file.

    Args:
        message: The specific data gap message.
        output_dir: Directory to write the flag log file.
    """
    logger.critical(f"CRITICAL DATA GAP: {message}")
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        flag_file = output_dir / "data_gap_flag.json"
        with open(flag_file, "w") as f:
            json.dump({"flag": "CRITICAL_DATA_GAP", "message": message}, f, indent=2)


def log_underpowered_flag(message: str, output_dir: Optional[Path] = None) -> None:
    """
    Log an underpowered study flag.

    Args:
        message: The specific underpowered message.
        output_dir: Directory to write the flag log file.
    """
    logger.warning(f"UNDERPOWERED: {message}")
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        flag_file = output_dir / "underpowered_flag.json"
        with open(flag_file, "w") as f:
            json.dump({"flag": "UNDERPOWERED", "message": message}, f, indent=2)


def log_under_determined_flag(message: str, output_dir: Optional[Path] = None) -> None:
    """
    Log an under-determined system flag.

    Args:
        message: The specific under-determined message.
        output_dir: Directory to write the flag log file.
    """
    logger.warning(f"UNDER-DETERMINED: {message}")
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        flag_file = output_dir / "under_determined_flag.json"
        with open(flag_file, "w") as f:
            json.dump({"flag": "UNDER-DETERMINED", "message": message}, f, indent=2)


def calculate_vif(features: pd.DataFrame) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.

    Args:
        features: DataFrame where columns are features.

    Returns:
        Series of VIF values indexed by feature name.
    """
    # Add intercept for VIF calculation
    X = features.copy()
    X['intercept'] = 1.0

    vif_data = pd.Series(index=features.columns, dtype=float)

    for col in features.columns:
        if col == 'intercept':
            continue
        # R^2 from regressing this feature against all others
        # We use the intercept column as a placeholder for the full matrix logic
        # But for VIF, we regress col against all OTHER cols
        other_cols = [c for c in features.columns if c != col]
        if not other_cols:
            vif_data[col] = 1.0
            continue

        # Use the intercept column to represent the full set of other predictors
        # Actually, we need to regress X[col] against X[other_cols]
        # Since we added 'intercept' to X, we need to be careful.
        # Let's rebuild X for the regression without the 'intercept' trick for now
        # and use statsmodels or manual OLS.
        # Simpler approach using numpy.linalg.lstsq:
        y = X[col].values
        # Predictors are all other original columns (excluding current and our added intercept)
        # But wait, X has the 'intercept' column we added.
        # Let's just use the original features dataframe for the regression matrix.
        # We need to regress feature i against all other features j != i.

        # Re-extract predictors from original features (excluding current col)
        # Note: features here is the input, which doesn't have our added 'intercept' yet?
        # Actually, let's just use the input `features` argument.
        # We need to construct the matrix X_other for the regression.
        # X_other = features.drop(columns=[col])
        # But we need an intercept in the regression model for VIF?
        # Standard VIF calculation: VIF_i = 1 / (1 - R_i^2)
        # where R_i^2 is from regressing X_i on all other X_j.
        # Usually, an intercept is included in this auxiliary regression.

        X_other = features.drop(columns=[col])
        # Add intercept for the auxiliary regression
        X_other_with_intercept = np.column_stack([np.ones(len(X_other)), X_other.values])

        try:
            # OLS: y = X_other * beta
            beta, residuals, rank, s = np.linalg.lstsq(X_other_with_intercept, y, rcond=None)
            if residuals.size > 0:
                ss_res = residuals[0]
            else:
                ss_res = 0.0
            ss_tot = np.sum((y - np.mean(y)) ** 2)

            if ss_tot == 0:
                r_squared = 0.0
            else:
                r_squared = 1 - (ss_res / ss_tot)

            vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else np.inf
            vif_data[col] = vif
        except np.linalg.LinAlgError:
            vif_data[col] = np.inf

    return vif_data


def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg procedure for False Discovery Rate control.

    Args:
        p_values: List of p-values.
        alpha: Significance level.

    Returns:
        Tuple of (list of booleans indicating significance, list of adjusted q-values).
    """
    n = len(p_values)
    if n == 0:
        return [], []

    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])

    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha

    # Determine significance (monotonicity check from the end)
    # Find the largest k such that p_(k) <= (k/m) * alpha
    # Then all p_(1)...p_(k) are significant.
    # To be safe and standard: compute adjusted p-values (q-values) first.

    # Calculate adjusted p-values (q-values)
    q_values = np.zeros(n)
    q_values[-1] = sorted_p[-1]
    for i in range(n - 2, -1, -1):
        q_values[i] = min(sorted_p[i] * n / (i + 1), q_values[i + 1])

    # Ensure q-values are within [0, 1]
    q_values = np.clip(q_values, 0, 1)

    # Map back to original order
    adjusted_p_values = np.zeros(n)
    for i, idx in enumerate(sorted_indices):
        adjusted_p_values[idx] = q_values[i]

    # Determine significance based on adjusted p-values
    significant = adjusted_p_values <= alpha

    return significant.tolist(), adjusted_p_values.tolist()


def generate_checksum(file_path: Path) -> str:
    """
    Generate SHA-256 checksum for a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def calculate_permanova_power(effect_size: float, n_per_group: int, alpha: float = 0.05, k_groups: int = 2) -> Tuple[float, int]:
    """
    Calculate statistical power for a PERMANOVA test using F-test approximation.

    Args:
        effect_size: Expected R-squared effect size.
        n_per_group: Number of samples per group.
        alpha: Significance level.
        k_groups: Number of groups.

    Returns:
        Tuple of (calculated power, minimum n_per_group needed for 0.8 power).
    """
    # Total sample size
    n_total = n_per_group * k_groups
    # Degrees of freedom
    df1 = k_groups - 1
    df2 = n_total - k_groups

    # Convert R^2 to F-statistic non-centrality parameter approximation
    # F = (R^2 / (k-1)) / ((1-R^2) / (N-k))
    # But statsmodels FTestAnovaPower expects effect_size as f-squared or similar?
    # Actually, FTestAnovaPower uses effect_size = sqrt(f^2) where f^2 = R^2 / (1-R^2)
    # So effect_size = sqrt(R^2 / (1-R^2))
    if effect_size >= 1.0:
        effect_size = 0.99 # Avoid division by zero

    f_squared = effect_size / (1.0 - effect_size)
    effect_size_f = np.sqrt(f_squared)

    power_analyzer = FTestAnovaPower()

    try:
        power = power_analyzer.power(effect_size=effect_size_f, nobs=n_total, alpha=alpha, k_groups=k_groups)
    except Exception:
        # Fallback if calculation fails
        power = 0.0

    # Estimate required n for 0.8 power
    # Simple binary search or approximation
    required_n = n_per_group
    min_n = 2
    max_n = 10000
    target_power = 0.8

    while min_n < max_n:
        mid_n = (min_n + max_n) // 2
        if mid_n < 2: mid_n = 2
        try:
            p = power_analyzer.power(effect_size=effect_size_f, nobs=mid_n * k_groups, alpha=alpha, k_groups=k_groups)
        except:
            p = 0.0

        if p >= target_power:
            required_n = mid_n
            max_n = mid_n - 1
        else:
            min_n = mid_n + 1

    return power, required_n


def validate_power_requirements(n_per_group: int, effect_size: float, alpha: float = 0.05, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Validate if the current sample size meets power requirements for PERMANOVA.

    Args:
        n_per_group: Current number of samples per group.
        effect_size: Expected effect size (R^2).
        alpha: Significance level.
        output_dir: Directory to write validation reports.

    Returns:
        Dictionary with power analysis results and flag.
    """
    power, n_needed = calculate_permanova_power(effect_size, n_per_group, alpha)

    result = {
        "power": float(power),
        "n_per_group": n_per_group,
        "effect_size": effect_size,
        "required_n_per_group": int(n_needed),
        "flag": "PASS" if power >= 0.8 else "UNDERPOWERED"
    }

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write power analysis report
        report_path = output_dir / "power_analysis_report.json"
        with open(report_path, "w") as f:
            json.dump(result, f, indent=2)

        # Write sample size validation
        validation_path = output_dir / "sample_size_validation.json"
        validation_data = {
            "current_n_per_group": n_per_group,
            "required_n_per_group": int(n_needed),
            "meets_requirements": power >= 0.8,
            "flag": result["flag"]
        }
        with open(validation_path, "w") as f:
            json.dump(validation_data, f, indent=2)

    return result
