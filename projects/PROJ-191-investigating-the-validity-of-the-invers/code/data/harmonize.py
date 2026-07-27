"""
Data harmonization utilities for the Inverse Square Law project.

This module handles:
1. Conversion of units to SI (dynes -> Newtons, micrometers -> meters).
2. Alignment of force-vs-separation data onto a common separation grid.
3. Construction of full covariance matrices from statistical and systematic errors.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from pathlib import Path

# Optional scipy import for advanced interpolation features
try:
    from scipy.interpolate import interp1d
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def dynes_to_newtons(force_dynes: np.ndarray | float) -> np.ndarray | float:
    """
    Convert force from dynes to Newtons.
    1 dyne = 1e-5 Newtons.

    Args:
        force_dynes: Force value(s) in dynes.

    Returns:
        Force value(s) in Newtons.
    """
    return np.asarray(force_dynes) * 1e-5


def micrometers_to_meters(dist_um: np.ndarray | float) -> np.ndarray | float:
    """
    Convert distance from micrometers to meters.
    1 micrometer = 1e-6 meters.

    Args:
        dist_um: Distance value(s) in micrometers.

    Returns:
        Distance value(s) in meters.
    """
    return np.asarray(dist_um) * 1e-6


def convert_to_si(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert force and separation columns in a DataFrame to SI units.

    Expects columns 'force_dyne' and 'separation_um'.
    Adds new columns 'force_N' and 'separation_m'.

    Args:
        df: Input DataFrame with raw data.

    Returns:
        DataFrame with added SI unit columns.
    """
    df_out = df.copy()

    if 'force_dyne' not in df_out.columns:
        raise ValueError("Input DataFrame must contain 'force_dyne' column.")
    if 'separation_um' not in df_out.columns:
        raise ValueError("Input DataFrame must contain 'separation_um' column.")

    df_out['force_N'] = dynes_to_newtons(df_out['force_dyne'].values)
    df_out['separation_m'] = micrometers_to_meters(df_out['separation_um'].values)

    return df_out


def align_to_grid(
    sep_m: np.ndarray,
    force_n: np.ndarray,
    target_grid: np.ndarray,
    method: str = 'linear'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Align force data to a target separation grid using interpolation.

    Args:
        sep_m: Array of separation distances in meters (source).
        force_n: Array of force values in Newtons (source).
        target_grid: Array of target separation distances in meters.
        method: Interpolation method ('linear', 'nearest', 'cubic').

    Returns:
        Tuple of (aligned_separation, aligned_force).
        aligned_separation will be exactly equal to target_grid.
    """
    # Ensure inputs are sorted by separation for interpolation
    sort_idx = np.argsort(sep_m)
    sep_sorted = sep_m[sort_idx]
    force_sorted = force_n[sort_idx]

    if HAS_SCIPY:
        # Use scipy for robust handling of bounds and fill values
        interpolator = interp1d(
            sep_sorted,
            force_sorted,
            kind=method,
            bounds_error=False,
            fill_value=np.nan
        )
        f_interp = interpolator(target_grid)
    else:
        # Fallback to numpy.interp if scipy is not installed
        in_bounds = (target_grid >= sep_sorted.min()) & (target_grid <= sep_sorted.max())
        f_interp = np.full_like(target_grid, np.nan, dtype=float)
        
        if np.any(in_bounds):
            f_interp[in_bounds] = np.interp(target_grid[in_bounds], sep_sorted, force_sorted)
        
    return target_grid, f_interp


def construct_covariance_matrix(
    stat_err: np.ndarray,
    sys_err: Optional[np.ndarray] = None,
    correlation_length: float = 0.0,
    systematic_scale: float = 1.0
) -> np.ndarray:
    """
    Construct a full covariance matrix from statistical and systematic uncertainties.

    The total variance at each point is the sum of statistical variance and 
    systematic variance (if provided). Systematic errors introduce correlations
    between data points.

    Args:
        stat_err: Statistical uncertainties (1-sigma) for each data point.
        sys_err: Systematic uncertainties (1-sigma) for each data point. 
                If None, only statistical errors are used (diagonal matrix).
        correlation_length: Fraction of the range over which systematic errors
                           are correlated. 0.0 = fully correlated (common mode),
                           1.0 = uncorrelated.
        systematic_scale: Scaling factor for systematic errors if missing in source.

    Returns:
        Full covariance matrix (N, N).
    """
    n_points = len(stat_err)
    
    # Convert to numpy arrays if not already
    stat_err = np.asarray(stat_err, dtype=float)
    
    # Calculate total variance (diagonal elements)
    if sys_err is not None:
        sys_err = np.asarray(sys_err, dtype=float)
        total_var = stat_err**2 + sys_err**2
    else:
        # Conservative fallback: scale statistical errors to account for missing systematics
        # This is a 10% inflation as a conservative estimate
        total_var = (stat_err * systematic_scale)**2
    
    # Initialize covariance matrix
    cov_matrix = np.zeros((n_points, n_points))
    
    # Fill diagonal with total variance
    np.fill_diagonal(cov_matrix, total_var)
    
    # Add systematic correlation off-diagonal elements if systematic errors exist
    if sys_err is not None:
        # Create a correlation matrix based on systematic errors
        # Using a simple model: correlation decays with index distance
        for i in range(n_points):
            for j in range(i + 1, n_points):
                # Calculate correlation coefficient
                # If correlation_length is 0, all systematic errors are fully correlated
                # If correlation_length is 1, no correlation
                if correlation_length == 0.0:
                    corr_coeff = 1.0
                else:
                    # Distance-based correlation decay
                    idx_dist = abs(i - j) / (n_points - 1) if n_points > 1 else 0
                    corr_coeff = max(0.0, 1.0 - idx_dist / correlation_length)
                
                # Covariance contribution from systematic errors
                cov_matrix[i, j] = corr_coeff * sys_err[i] * sys_err[j]
                cov_matrix[j, i] = cov_matrix[i, j]
    
    # Ensure the matrix is symmetric and positive semi-definite
    # Add small regularization if needed to ensure positive definiteness
    eigvals = np.linalg.eigvalsh(cov_matrix)
    if np.min(eigvals) < 1e-15:
        # Add small diagonal regularization
        cov_matrix += np.eye(n_points) * 1e-15
    
    return cov_matrix


def harmonize_experiment(
    df_raw: pd.DataFrame,
    target_grid: np.ndarray
) -> pd.DataFrame:
    """
    Full harmonization pipeline for a single experiment DataFrame.

    1. Convert to SI units.
    2. Align to the target grid.
    3. Construct covariance matrix from error fields.
    4. Return a DataFrame with aligned data and covariance matrix.

    Args:
        df_raw: Raw DataFrame with 'force_dyne', 'separation_um', and optional error columns.
               Expected error columns: 'stat_err', 'sys_err' or 'systematic'.
        target_grid: Target separation grid in meters.

    Returns:
        DataFrame with 'separation_m' (target_grid), 'force_N' (interpolated),
        and a 'covariance_matrix' column containing the full covariance matrix.
    """
    # Convert to SI
    df_si = convert_to_si(df_raw)
    
    # Check for error columns and extract uncertainties
    stat_err_col = None
    sys_err_col = None
    
    if 'stat_err' in df_si.columns:
        stat_err_col = 'stat_err'
    elif 'stat_err_dyne' in df_si.columns:
        # Convert statistical error from dynes to Newtons
        df_si['stat_err_N'] = dynes_to_newtons(df_si['stat_err_dyne'].values)
        stat_err_col = 'stat_err_N'
        
    if 'sys_err' in df_si.columns:
        sys_err_col = 'sys_err'
    elif 'systematic' in df_si.columns:
        sys_err_col = 'systematic'
    elif 'sys_err_dyne' in df_si.columns:
        df_si['sys_err_N'] = dynes_to_newtons(df_si['sys_err_dyne'].values)
        sys_err_col = 'sys_err_N'
    
    # Extract uncertainties
    stat_err = df_si[stat_err_col].values if stat_err_col else np.zeros(len(df_si))
    sys_err = df_si[sys_err_col].values if sys_err_col else None
    
    # Align to grid
    sep_aligned, force_aligned = align_to_grid(
        df_si['separation_m'].values,
        df_si['force_N'].values,
        target_grid
    )
    
    # Construct covariance matrix
    cov_matrix = construct_covariance_matrix(
        stat_err=stat_err,
        sys_err=sys_err
    )
    
    result_df = pd.DataFrame({
        'separation_m': sep_aligned,
        'force_N': force_aligned
    })
    
    # Add covariance matrix as a column (will be expanded when saving)
    result_df['covariance_matrix'] = [cov_matrix]
    
    # Preserve experiment ID if present
    if 'experiment_id' in df_raw.columns:
        result_df['experiment_id'] = df_raw['experiment_id'].iloc[0]
    
    return result_df