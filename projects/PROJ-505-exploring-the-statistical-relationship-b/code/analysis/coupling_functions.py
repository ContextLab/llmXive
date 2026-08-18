"""
Coupling functions module for solar wind - magnetosphere interaction metrics.

This module derives bulk-parameter coupling functions including:
- Akasofu Epsilon (ε): Energy coupling function
- Newell Function (dΦ_MP/dt): Magnetospheric convection proxy
- v*B_s: Simple solar wind-magnetosphere coupling
- v*B_T: Total transverse magnetic field coupling

These functions are derived from aligned solar wind and geomagnetic data.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, Any

from utils.logging import AnalysisError, get_logger, log_duration

logger = get_logger(__name__)


@log_duration
def compute_akasofu_epsilon(
    df: pd.DataFrame,
    v_col: str = 'v',
    b_col: str = 'b',
    bz_col: str = 'bz',
    theta_col: Optional[str] = None,
    alfvén_radius: float = 2.0,
    epsilon_floor: float = 1e-6
) -> pd.Series:
    """
    Compute the Akasofu Epsilon function (ε).

    The Akasofu epsilon function estimates the rate of energy transfer
    from the solar wind to the magnetosphere.

    Formula: ε = v * B^2 * sin^4(θ/2) * l_0^2

    Where:
    - v: Solar wind speed (km/s)
    - B: IMF magnitude (nT)
    - θ: Clock angle of IMF
    - l_0: Effective coupling length (typically ~7 RE, converted to km)

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing solar wind parameters
    v_col : str
        Column name for solar wind speed (km/s)
    b_col : str
        Column name for IMF magnitude (nT)
    bz_col : str
        Column name for IMF Bz component (nT)
    theta_col : str, optional
        Column name for clock angle (radians). If None, computed from bz/bt
    alfvén_radius : float
        Alfvén radius in RE (default 2.0)
    epsilon_floor : float
        Minimum value to avoid numerical issues

    Returns
    -------
    pd.Series
        Epsilon values in units of Watts (scaled)
    """
    try:
        v = df[v_col].values
        b = df[b_col].values
        bz = df[bz_col].values

        # Compute transverse IMF component (Bt)
        bt = np.sqrt(np.maximum(b**2 - bz**2, 0))

        # Compute clock angle if not provided
        if theta_col is None:
            # sin(θ/2) = sqrt((1 - cos(θ))/2)
            # cos(θ) = bz / B (for southward component)
            # For southward IMF, bz < 0, so we use absolute value for magnitude
            cos_theta = bz / np.maximum(b, 1e-10)
            cos_theta = np.clip(cos_theta, -1.0, 1.0)
            sin_half_theta_sq = (1.0 - cos_theta) / 2.0
            sin_half_theta_sq = np.maximum(sin_half_theta_sq, 0.0)
        else:
            theta = df[theta_col].values
            sin_half_theta_sq = np.sin(theta / 2.0) ** 2

        # Effective coupling length l_0 (in km)
        # 1 RE ≈ 6371 km, l_0 is typically ~7 RE
        l_0_km = alfvén_radius * 6371.0
        l_0_squared = l_0_km ** 2

        # Epsilon = v * B^2 * sin^4(θ/2) * l_0^2
        # Note: sin^4(θ/2) = (sin^2(θ/2))^2
        epsilon = v * (b ** 2) * (sin_half_theta_sq ** 2) * l_0_squared

        # Apply floor to avoid numerical issues
        epsilon = np.maximum(epsilon, epsilon_floor)

        return pd.Series(epsilon, index=df.index, name='epsilon')

    except Exception as e:
        raise AnalysisError(f"Failed to compute Akasofu epsilon: {str(e)}") from e


@log_duration
def compute_newell_function(
    df: pd.DataFrame,
    v_col: str = 'v',
    bz_col: str = 'bz',
    bt_col: str = 'bt',
    epsilon_floor: float = 1e-6
) -> pd.Series:
    """
    Compute the Newell function (dΦ_MP/dt).

    The Newell coupling function is an empirical measure of magnetospheric
    convection, derived from solar wind parameters.

    Formula: dΦ_MP/dt = v^(4/3) * B_T^(2/3) * sin^(8/3)(θ/2)

    Where:
    - v: Solar wind speed (km/s)
    - B_T: Transverse IMF component (nT)
    - θ: Clock angle of IMF

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing solar wind parameters
    v_col : str
        Column name for solar wind speed (km/s)
    bz_col : str
        Column name for IMF Bz component (nT)
    bt_col : str
        Column name for transverse IMF component (nT)
    epsilon_floor : float
        Minimum value to avoid numerical issues

    Returns
    -------
    pd.Series
        Newell function values (mV)
    """
    try:
        v = df[v_col].values
        bz = df[bz_col].values
        bt = df[bt_col].values

        # Compute clock angle term: sin^(8/3)(θ/2)
        # sin(θ/2) = sqrt((1 - bz/B) / 2)
        # For southward IMF (bz < 0), this gives larger values
        b_total = np.sqrt(bt**2 + bz**2)
        b_total = np.maximum(b_total, 1e-10)

        cos_theta = bz / b_total
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        sin_half_theta_sq = (1.0 - cos_theta) / 2.0
        sin_half_theta_sq = np.maximum(sin_half_theta_sq, 0.0)

        # sin^(8/3)(θ/2) = (sin^2(θ/2))^(4/3)
        sin_term = sin_half_theta_sq ** (4.0 / 3.0)

        # dΦ_MP/dt = v^(4/3) * B_T^(2/3) * sin^(8/3)(θ/2)
        newell = (v ** (4.0 / 3.0)) * (bt ** (2.0 / 3.0)) * sin_term

        # Apply floor
        newell = np.maximum(newell, epsilon_floor)

        return pd.Series(newell, index=df.index, name='newell')

    except Exception as e:
        raise AnalysisError(f"Failed to compute Newell function: {str(e)}") from e


@log_duration
def compute_v_bs(
    df: pd.DataFrame,
    v_col: str = 'v',
    bz_col: str = 'bz',
    epsilon_floor: float = 1e-6
) -> pd.Series:
    """
    Compute the v*B_s coupling function.

    Simple coupling function using solar wind speed and southward IMF component.

    Formula: v * B_s

    Where:
    - v: Solar wind speed (km/s)
    - B_s: Southward IMF component (nT), max(0, -Bz)

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing solar wind parameters
    v_col : str
        Column name for solar wind speed (km/s)
    bz_col : str
        Column name for IMF Bz component (nT)
    epsilon_floor : float
        Minimum value to avoid numerical issues

    Returns
    -------
    pd.Series
        v*B_s values
    """
    try:
        v = df[v_col].values
        bz = df[bz_col].values

        # B_s is the southward component: max(0, -Bz)
        b_s = np.maximum(0.0, -bz)

        v_bs = v * b_s

        # Apply floor (but allow zero for purely northward IMF)
        # Only apply floor when b_s > 0
        mask = b_s > 0
        v_bs[mask] = np.maximum(v_bs[mask], epsilon_floor)

        return pd.Series(v_bs, index=df.index, name='v_bs')

    except Exception as e:
        raise AnalysisError(f"Failed to compute v*B_s: {str(e)}") from e


@log_duration
def compute_v_bt(
    df: pd.DataFrame,
    v_col: str = 'v',
    bt_col: str = 'bt',
    epsilon_floor: float = 1e-6
) -> pd.Series:
    """
    Compute the v*B_T coupling function.

    Coupling function using solar wind speed and total transverse IMF.

    Formula: v * B_T

    Where:
    - v: Solar wind speed (km/s)
    - B_T: Total transverse IMF component (nT)

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing solar wind parameters
    v_col : str
        Column name for solar wind speed (km/s)
    bt_col : str
        Column name for transverse IMF component (nT)
    epsilon_floor : float
        Minimum value to avoid numerical issues

    Returns
    -------
    pd.Series
        v*B_T values
    """
    try:
        v = df[v_col].values
        bt = df[bt_col].values

        v_bt = v * bt

        # Apply floor
        v_bt = np.maximum(v_bt, epsilon_floor)

        return pd.Series(v_bt, index=df.index, name='v_bt')

    except Exception as e:
        raise AnalysisError(f"Failed to compute v*B_T: {str(e)}") from e


@log_duration
def compute_all_coupling_functions(
    df: pd.DataFrame,
    v_col: str = 'v',
    b_col: str = 'b',
    bz_col: str = 'bz',
    bt_col: str = 'bt',
    theta_col: Optional[str] = None,
    epsilon_floor: float = 1e-6
) -> pd.DataFrame:
    """
    Compute all coupling functions for the given DataFrame.

    This is a convenience function that computes:
    - Akasofu Epsilon (ε)
    - Newell Function (dΦ_MP/dt)
    - v*B_s
    - v*B_T

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing aligned solar wind parameters
    v_col : str
        Column name for solar wind speed (km/s)
    b_col : str
        Column name for IMF magnitude (nT)
    bz_col : str
        Column name for IMF Bz component (nT)
    bt_col : str
        Column name for transverse IMF component (nT)
    theta_col : str, optional
        Column name for clock angle (radians)
    epsilon_floor : float
        Minimum value to avoid numerical issues

    Returns
    -------
    pd.DataFrame
        DataFrame with additional coupling function columns
    """
    try:
        # Validate required columns
        required_cols = [v_col, b_col, bz_col, bt_col]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns for coupling functions: {missing}")

        # Compute individual coupling functions
        df = df.copy()
        df['epsilon'] = compute_akasofu_epsilon(
            df, v_col, b_col, bz_col, theta_col, epsilon_floor=epsilon_floor
        )
        df['newell'] = compute_newell_function(
            df, v_col, bz_col, bt_col, epsilon_floor=epsilon_floor
        )
        df['v_bs'] = compute_v_bs(df, v_col, bz_col, epsilon_floor=epsilon_floor)
        df['v_bt'] = compute_v_bt(df, v_col, bt_col, epsilon_floor=epsilon_floor)

        logger.info(f"Computed coupling functions: epsilon, newell, v_bs, v_bt")

        return df

    except Exception as e:
        raise AnalysisError(f"Failed to compute all coupling functions: {str(e)}") from e


def get_coupling_function_columns() -> list:
    """
    Return the list of coupling function column names.

    Returns
    -------
    list
        Column names for coupling functions
    """
    return ['epsilon', 'newell', 'v_bs', 'v_bt']


def main():
    """
    Main function to demonstrate coupling function computation.
    This is typically called from a pipeline script.
    """
    import sys
    import argparse

    from ingestion.align import align_data
    from utils.io import load_parquet, save_parquet
    from utils.mkdirs import ensure_dirs
    from config import get_config

    parser = argparse.ArgumentParser(description='Compute coupling functions from aligned data')
    parser.add_argument('--input', type=str, help='Input aligned data file')
    parser.add_argument('--output', type=str, help='Output file with coupling functions')
    parser.add_argument('--config', type=str, default=None, help='Config file path')
    args = parser.parse_args()

    config = get_config(args.config)

    # Load aligned data
    input_path = args.input or config.get('paths', {}).get('aligned_data', 'data/processed/aligned_hourly.parquet')

    if not input_path or input_path.endswith('.csv'):
        # Try to find parquet file
        import glob
        parquet_files = glob.glob('data/processed/*.parquet')
        if parquet_files:
            input_path = parquet_files[0]
        else:
            logger.error(f"No aligned data found at {input_path}")
            sys.exit(1)

    logger.info(f"Loading aligned data from {input_path}")
    df = load_parquet(input_path)

    # Compute coupling functions
    logger.info("Computing coupling functions...")
    df_with_coupling = compute_all_coupling_functions(df)

    # Save output
    output_path = args.output or config.get('paths', {}).get('coupling_data', 'data/processed/coupling_functions.parquet')
    ensure_dirs(output_path)

    logger.info(f"Saving coupling functions to {output_path}")
    save_parquet(df_with_coupling, output_path)

    logger.info(f"Successfully computed {len(get_coupling_function_columns())} coupling functions")
    logger.info(f"Output columns: {list(df_with_coupling.columns)}")


if __name__ == '__main__':
    main()