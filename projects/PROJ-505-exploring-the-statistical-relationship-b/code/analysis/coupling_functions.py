"""
Utility module for computing solar‑wind coupling functions.
Provides vectorised implementations of the Akasofu ε and Newell
dΦ/dt functions, as well as helper terms V·B_s and V·B_t.
"""
import argparse
from pathlib import Path
from typing import Union, Optional

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger
from code.utils.logging import AnalysisError, get_logger as get_analysis_logger, log_duration

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _extract_series(df: pd.DataFrame, name_variants: list[str]) -> pd.Series:
    """
    Retrieve a Series from a DataFrame given a list of possible column names.
    Raises KeyError if none are found.
    """
    for name in name_variants:
        if name in df.columns:
            return df[name]
    raise KeyError(f"None of the expected column names {name_variants} found in DataFrame.")

# ----------------------------------------------------------------------
# Coupling function implementations
# ----------------------------------------------------------------------
def compute_akasofu_epsilon(
    V: Union[pd.Series, pd.DataFrame],
    Bt: Optional[pd.Series] = None,
    By: Optional[pd.Series] = None,
    Bz: Optional[pd.Series] = None,
    theta: Optional[Union[pd.Series, pd.DataFrame]] = None,
) -> pd.Series:
    """
    Compute the Akasofu ε coupling function.

    ε = V * B_s^2 * sin⁴(θ/2)

    Parameters are tolerant to being supplied either as a DataFrame
    (with column‑name variants) or as explicit Series.
    """
    # Resolve V
    if isinstance(V, pd.DataFrame):
        V_series = _extract_series(V, ["v_sw", "V"])
    else:
        V_series = V

    # Resolve B_s (southward component). Preference order:
    # 1. Explicit Bt/Bs Series supplied.
    # 2. Column "B_s" in DataFrame.
    # 3. Compute from By/Bz if available.
    if isinstance(Bt, pd.DataFrame):
        df = Bt
        if "B_s" in df.columns:
            Bs_series = df["B_s"]
        else:
            By_series = _extract_series(df, ["By"])
            Bz_series = _extract_series(df, ["Bz"])
            Bs_series = np.sqrt(By_series ** 2 + Bz_series ** 2)
    elif Bt is not None:
        Bs_series = Bt
    else:
        # Try to find B_s directly in the DataFrame (if V was a DataFrame)
        if isinstance(V, pd.DataFrame) and "B_s" in V.columns:
            Bs_series = V["B_s"]
        else:
            # Need By/Bz to compute B_s
            if By is None or Bz is None:
                # Attempt to pull By/Bz from V if it is a DataFrame
                if isinstance(V, pd.DataFrame):
                    By = _extract_series(V, ["By"])
                    Bz = _extract_series(V, ["Bz"])
                else:
                    raise KeyError("By and Bz are required to compute B_s when not provided.")
            Bs_series = np.sqrt(By ** 2 + Bz ** 2)

    # Resolve theta (clock angle). Preference:
    # 1. Provided explicitly.
    # 2. Extract from DataFrame if V is a DataFrame.
    # 3. Approximate from By/Bz if possible.
    if theta is None:
        if isinstance(V, pd.DataFrame):
            # Look for a column named 'theta'
            if "theta" in V.columns:
                theta_series = V["theta"]
            else:
                # Approximate using By/Bz if present
                try:
                    By_series = _extract_series(V, ["By"])
                    Bz_series = _extract_series(V, ["Bz"])
                    theta_series = np.degrees(np.arctan2(By_series, Bz_series)) % 360
                except KeyError:
                    theta_series = pd.Series(0, index=V_series.index)
        else:
            # No DataFrame context – default to zero
            theta_series = pd.Series(0, index=V_series.index)
    else:
        if isinstance(theta, pd.DataFrame):
            theta_series = _extract_series(theta, ["theta"])
        else:
            theta_series = theta

    # Vectorised ε calculation
    sin_term = np.sin(np.radians(theta_series / 2.0))
    epsilon = V_series * (Bs_series ** 2) * (sin_term ** 4)
    epsilon = epsilon.fillna(0.0)
    return epsilon

def compute_newell_function(
    V: Union[pd.Series, pd.DataFrame],
    Bt: Optional[pd.Series] = None,
    Bz: Optional[pd.Series] = None,
    theta: Optional[Union[pd.Series, pd.DataFrame]] = None,
) -> pd.Series:
    """
    Compute the Newell dΦ/dt coupling function.

    dΦ/dt = V^(4/3) * B_t^(2/3) * sin^(8/3)(θ/2)

    Accepts either a full DataFrame (with column variants) or
    individual Series.
    """
    # Resolve V
    if isinstance(V, pd.DataFrame):
        V_series = _extract_series(V, ["v_sw", "V"])
    else:
        V_series = V

    # Resolve B_t (total transverse field). Preference order:
    # 1. Explicit Bt Series.
    # 2. Column "B_t" in DataFrame.
    # 3. Compute from By/Bz if available.
    if isinstance(Bt, pd.DataFrame):
        df = Bt
        if "B_t" in df.columns:
            Bt_series = df["B_t"]
        else:
            By_series = _extract_series(df, ["By"])
            Bz_series = _extract_series(df, ["Bz"])
            Bt_series = np.sqrt(By_series ** 2 + Bz_series ** 2)
    elif Bt is not None:
        Bt_series = Bt
    else:
        # Try to find B_t directly in the DataFrame (if V was a DataFrame)
        if isinstance(V, pd.DataFrame) and "B_t" in V.columns:
            Bt_series = V["B_t"]
        else:
            # Need By/Bz to compute B_t
            if Bz is None:
                if isinstance(V, pd.DataFrame):
                    By = _extract_series(V, ["By"])
                    Bz = _extract_series(V, ["Bz"])
                else:
                    raise KeyError("By and Bz are required to compute B_t when not provided.")
            else:
                # By may still be None – try to extract from V if possible
                if isinstance(V, pd.DataFrame):
                    By = _extract_series(V, ["By"])
            Bt_series = np.sqrt(By ** 2 + Bz ** 2)

    # Resolve theta
    if theta is None:
        if isinstance(V, pd.DataFrame):
            if "theta" in V.columns:
                theta_series = V["theta"]
            else:
                try:
                    By_series = _extract_series(V, ["By"])
                    Bz_series = _extract_series(V, ["Bz"])
                    theta_series = np.degrees(np.arctan2(By_series, Bz_series)) % 360
                except KeyError:
                    theta_series = pd.Series(0, index=V_series.index)
        else:
            theta_series = pd.Series(0, index=V_series.index)
    else:
        if isinstance(theta, pd.DataFrame):
            theta_series = _extract_series(theta, ["theta"])
        else:
            theta_series = theta

    sin_term = np.sin(np.radians(theta_series / 2.0))
    newell = (V_series ** (4.0 / 3.0)) * (Bt_series ** (2.0 / 3.0)) * (sin_term ** (8.0 / 3.0))
    newell = newell.fillna(0.0)
    return newell

def compute_v_bs(
    V: Union[pd.Series, pd.DataFrame],
    Bs: Optional[pd.Series] = None,
) -> pd.Series:
    """
    Compute V * B_s term. Negative B_s values are set to zero
    (physically, only southward IMF contributes).
    """
    if isinstance(V, pd.DataFrame):
        V_series = _extract_series(V, ["v_sw", "V"])
    else:
        V_series = V

    if isinstance(Bs, pd.DataFrame):
        df = Bs
        if "B_s" in df.columns:
            Bs_series = df["B_s"]
        else:
            By_series = _extract_series(df, ["By"])
            Bz_series = _extract_series(df, ["Bz"])
            Bs_series = np.sqrt(By_series ** 2 + Bz_series ** 2)
    elif Bs is not None:
        Bs_series = Bs
    else:
        raise KeyError("Bs series is required for compute_v_bs.")

    result = V_series.copy()
    mask = Bs_series >= 0
    result[~mask] = 0.0
    return result

def compute_v_bt(
    V: Union[pd.Series, pd.DataFrame],
    Bt: Optional[pd.Series] = None,
) -> pd.Series:
    """
    Compute V * B_t term.
    """
    if isinstance(V, pd.DataFrame):
        V_series = _extract_series(V, ["v_sw", "V"])
    else:
        V_series = V

    if isinstance(Bt, pd.DataFrame):
        df = Bt
        if "B_t" in df.columns:
            Bt_series = df["B_t"]
        else:
            By_series = _extract_series(df, ["By"])
            Bz_series = _extract_series(df, ["Bz"])
            Bt_series = np.sqrt(By_series ** 2 + Bz_series ** 2)
    elif Bt is not None:
        Bt_series = Bt
    else:
        raise KeyError("Bt series is required for compute_v_bt.")

    return V_series * Bt_series

def compute_all_coupling_functions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all coupling function columns (epsilon, newell) to the DataFrame.
    Returns a new DataFrame containing only the added columns plus the
    original index.
    """
    epsilon = compute_akasofu_epsilon(df)
    newell = compute_newell_function(df)
    result = df.copy()
    result["epsilon"] = epsilon
    result["newell"] = newell
    return result

def get_coupling_function_columns() -> list:
    """
    Return the list of coupling function column names added by
    ``compute_all_coupling_functions``.
    """
    return ["epsilon", "newell"]

def compute_epsilon(row: pd.Series) -> float:
    """
    Row‑wise wrapper for the Akasofu epsilon calculation.
    Accepts a Series representing a single observation.
    """
    return compute_akasofu_epsilon(row.to_frame().T).iloc[0]

def compute_newell(row: pd.Series) -> float:
    """
    Row‑wise wrapper for the Newell dΦ/dt coupling function.
    Accepts a Series representing a single observation.
    """
    return compute_newell_function(row.to_frame().T).iloc[0]

def _process_and_write(input_path: Path, output_path: Path) -> None:
    """
    Load the aligned hourly dataset, compute all coupling functions,
    and write the enriched DataFrame to ``output_path`` as Parquet.
    """
    df = pd.read_parquet(input_path)
    enriched = compute_all_coupling_functions(df)
    enriched.to_parquet(output_path, index=False)

def main() -> None:
    """
    Command‑line interface.
    By default operates on the standard project layout:
    - Input: ``data/processed/aligned_hourly.parquet``
    - Output: ``data/processed/with_coupling.parquet``
    """
    parser = argparse.ArgumentParser(description="Compute coupling functions.")
    parser.add_argument(
        "--input",
        type=str,
        default=str(paths.data("processed", "aligned_hourly.parquet")),
        help="Path to aligned hourly parquet file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(paths.data("processed", "with_coupling.parquet")),
        help="Path where the enriched parquet will be saved.",
    )
    args = parser.parse_args()
    _process_and_write(Path(args.input), Path(args.output))
    log.info(f"Coupling functions written to {args.output}")

if __name__ == "__main__":
    main()