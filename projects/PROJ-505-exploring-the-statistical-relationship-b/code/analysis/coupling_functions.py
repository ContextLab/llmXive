"""
Coupling function calculations for solar‑wind / magnetosphere interaction.
Provides functions to compute Akasofu epsilon, Newell function,
and simple V * B products. All functions operate on pandas Series
and return a Series aligned with the input.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, Any

# Updated import path
from code.utils.logging import AnalysisError, get_logger, log_duration

logger = get_logger(__name__)


def compute_akasofu_epsilon(
    V: pd.Series,
    Bt: pd.Series,
    By: pd.Series,
    Bz: pd.Series,
    theta: Optional[pd.Series] = None,
) -> pd.Series:
    """
    Compute the Akasofu epsilon coupling function.

    ε = V * B^2 * l0^2 * sin^4(theta/2)
    where B = sqrt(By^2 + Bz^2) and l0 = 7 RE (taken as constant).
    """
    # Physical constants
    l0 = 7.0  # Earth radii, dimensionless scaling factor

    B = np.sqrt(By**2 + Bz**2)
    if theta is None:
        # If theta not supplied, approximate with IMF clock angle
        theta = np.arctan2(By, Bz).abs()
    sin_term = np.sin(theta / 2.0) ** 4
    epsilon = V * (B ** 2) * (l0 ** 2) * sin_term
    return epsilon


def compute_newell_function(
    V: pd.Series,
    Bt: pd.Series,
    Bz: pd.Series,
    theta: Optional[pd.Series] = None,
) -> pd.Series:
    """
    Compute the Newell coupling function.

    dΦ_MP/dt = V^(4/3) * Bt^(2/3) * sin^(8/3)(θ/2)
    """
    if theta is None:
        # Approximate clock angle as above
        theta = np.arctan2(Bt, Bz).abs()
    sin_term = np.sin(theta / 2.0) ** (8.0 / 3.0)
    newell = (V ** (4.0 / 3.0)) * (Bt ** (2.0 / 3.0)) * sin_term
    return newell


def compute_v_bs(V: pd.Series, Bs: pd.Series) -> pd.Series:
    """
    Compute V * Bs coupling term.
    """
    return V * Bs


def compute_v_bt(V: pd.Series, Bt: pd.Series) -> pd.Series:
    """
    Compute V * Bt coupling term.
    """
    return V * Bt


def compute_all_coupling_functions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all coupling function columns to the DataFrame.
    Expects columns: V, Bt, By, Bz.
    """
    required = {"V", "Bt", "By", "Bz"}
    missing = required - set(df.columns)
    if missing:
        raise AnalysisError(f"Missing required columns for coupling functions: {missing}")

    df = df.copy()
    df["epsilon"] = compute_akasofu_epsilon(df["V"], df["Bt"], df["By"], df["Bz"])
    df["newell"] = compute_newell_function(df["V"], df["Bt"], df["Bz"])
    df["v_bs"] = compute_v_bs(df["V"], df["Bt"])  # Using Bt as proxy for Bs
    df["v_bt"] = compute_v_bt(df["V"], df["Bt"])
    return df


def get_coupling_function_columns() -> list:
    """
    Return a list of coupling function column names added by compute_all_coupling_functions.
    """
    return ["epsilon", "newell", "v_bs", "v_bt"]


def main() -> None:
    """Entry point for debugging coupling function calculations."""
    logger.info("Coupling function module loaded.")


if __name__ == "__main__":
    main()
