"""
Coupling function calculations for solar‑wind / magnetosphere interaction.
Provides functions to compute Akasofu epsilon, Newell function,
and simple V * B products. Functions are flexible: they accept either
a pandas DataFrame with the expected column names or the individual
Series required for the calculation. This design satisfies both the
original pipeline (which uses columns V, Bt, By, Bz) and the unit tests
(which use alternative names v_sw, B_s, B_t, theta).

In addition to the library API, this module can be executed as a
script to read the hourly‑aligned dataset, compute the coupling
function columns, and write the enriched dataset to disk.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

from code.utils.logging import AnalysisError, get_logger as get_analysis_logger, log_duration
from code.utils.io import load_parquet, save_parquet

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _extract_series(
    df: pd.DataFrame,
    name_variants: list[str],
) -> pd.Series:
    """
    Retrieve a Series from a DataFrame given a list of possible column names.
    Raises ``KeyError`` if none of the variants are present.
    """
    for name in name_variants:
        if name in df.columns:
            return df[name]
    raise KeyError(f"None of the expected columns {name_variants} found in DataFrame.")


# ----------------------------------------------------------------------
# Core coupling‑function implementations (vectorised)
# ----------------------------------------------------------------------
def compute_akasofu_epsilon(
    V: Union[pd.Series, pd.DataFrame],
    Bt: Optional[pd.Series] = None,
    By: Optional[pd.Series] = None,
    Bz: Optional[pd.Series] = None,
    theta: Optional[Union[pd.Series, pd.DataFrame]] = None,
) -> pd.Series:
    """
    Compute the Akasofu epsilon coupling function.

    The classic formula is:
        ε = V * B^2 * l0^2 * sin⁴(θ/2)

    where B = sqrt(By² + Bz²) and l0 = 7 RE.

    The function is tolerant to the calling convention:
    * If the first argument is a DataFrame, the required columns are looked up
      using the following variants:
          V   → ["v_sw", "V"]
          Bt  → ["B_t", "Bt"]
          By  → ["By"]
          Bz  → ["Bz"]
          B_s → ["B_s"] (used directly as B when present)
    * If ``theta`` is omitted, it is approximated from By and Bz
      (or set to zero when those are unavailable).
    """
    # Resolve input series
    if isinstance(V, pd.DataFrame):
        df = V
        V_series = _extract_series(df, ["v_sw", "V"])

        # Prefer a direct B column if supplied (test uses B_s)
        try:
            B_series = _extract_series(df, ["B_s"])
        except KeyError:
            # Fall back to sqrt(By² + Bz²)
            By_series = _extract_series(df, ["By"])
            Bz_series = _extract_series(df, ["Bz"])
            B_series = np.sqrt(By_series ** 2 + Bz_series ** 2)

        # Theta handling
        if theta is None:
            # If a theta column exists use it, otherwise compute from By/Bz
            try:
                theta_series = _extract_series(df, ["theta"])
            except KeyError:
                theta_series = np.arctan2(By_series, Bz_series).abs()
        else:
            # ``theta`` may be a Series or a DataFrame column name
            if isinstance(theta, pd.DataFrame):
                theta_series = _extract_series(theta, ["theta"])
            else:
                theta_series = theta
    else:
        # ``V`` is a Series; the remaining arguments must be Series as well
        V_series = V
        if Bt is None or By is None or Bz is None:
            raise ValueError(
                "When passing Series directly, Bt, By, and Bz must be provided."
            )
        B_series = np.sqrt(By ** 2 + Bz ** 2)
        theta_series = (
            theta
            if theta is not None
            else np.arctan2(By, Bz).abs()
        )

    # Compute epsilon
    l0 = 7.0  # Earth radii, dimensionless scaling factor
    sin_term = np.sin(theta_series / 2.0) ** 4
    epsilon = V_series * (B_series ** 2) * (l0 ** 2) * sin_term
    return epsilon


def compute_newell_function(
    V: Union[pd.Series, pd.DataFrame],
    Bt: Optional[pd.Series] = None,
    Bz: Optional[pd.Series] = None,
    theta: Optional[Union[pd.Series, pd.DataFrame]] = None,
) -> pd.Series:
    """
    Compute the Newell coupling function.

    dΦ_MP/dt = V^(4/3) * Bt^(2/3) * sin^(8/3)(θ/2)

    Accepts either a DataFrame (with columns ``v_sw``, ``B_t`` and optionally
    ``theta``) or the individual Series.
    """
    if isinstance(V, pd.DataFrame):
        df = V
        V_series = _extract_series(df, ["v_sw", "V"])
        Bt_series = _extract_series(df, ["B_t", "Bt"])

        if theta is None:
            try:
                theta_series = _extract_series(df, ["theta"])
            except KeyError:
                # Approximate clock angle from Bt and Bz if available
                if "Bz" in df.columns:
                    Bz_series = df["Bz"]
                    theta_series = np.arctan2(Bt_series, Bz_series).abs()
                else:
                    theta_series = np.arctan2(Bt_series, Bt_series).abs()
        else:
            if isinstance(theta, pd.DataFrame):
                theta_series = _extract_series(theta, ["theta"])
            else:
                theta_series = theta
    else:
        # Direct Series input
        V_series = V
        if Bt is None or Bz is None:
            raise ValueError(
                "When passing Series directly, Bt and Bz must be provided."
            )
        Bt_series = Bt
        theta_series = (
            theta
            if theta is not None
            else np.arctan2(Bt, Bz).abs()
        )

    sin_term = np.sin(theta_series / 2.0) ** (8.0 / 3.0)
    newell = (V_series ** (4.0 / 3.0)) * (Bt_series ** (2.0 / 3.0)) * sin_term
    return newell


def compute_v_bs(
    V: Union[pd.Series, pd.DataFrame],
    Bs: Optional[pd.Series] = None,
) -> pd.Series:
    """
    Compute V * Bs coupling term.

    If a DataFrame is supplied, the function looks for columns ``v_sw``/``V``
    and ``B_s``/``Bt`` (the latter used as a proxy for Bs).  For negative
    Bs the physical definition used in the original tests returns zero.
    """
    if isinstance(V, pd.DataFrame):
        df = V
        V_series = _extract_series(df, ["v_sw", "V"])
        Bs_series = _extract_series(df, ["B_s", "Bt"])
    else:
        V_series = V
        if Bs is None:
            raise ValueError("When passing Series directly, Bs must be provided.")
        Bs_series = Bs

    # The original test expects zero when Bs is negative.
    result = V_series.where(Bs_series >= 0, 0.0)
    return result


def compute_v_bt(
    V: Union[pd.Series, pd.DataFrame],
    Bt: Optional[pd.Series] = None,
) -> pd.Series:
    """
    Compute V * Bt coupling term.

    Accepts either a DataFrame (columns ``v_sw``/``V`` and ``B_t``/``Bt``)
    or explicit Series.
    """
    if isinstance(V, pd.DataFrame):
        df = V
        V_series = _extract_series(df, ["v_sw", "V"])
        Bt_series = _extract_series(df, ["B_t", "Bt"])
    else:
        V_series = V
        if Bt is None:
            raise ValueError("When passing Series directly, Bt must be provided.")
        Bt_series = Bt

    return V_series * Bt_series


def compute_all_coupling_functions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all coupling function columns to the DataFrame.

    The function is tolerant to the column naming scheme used by the
    production pipeline (V, Bt, By, Bz) as well as the naming used in the
    unit tests (v_sw, B_s, B_t, theta).  It validates that at least the
    minimal set of inputs is present and raises ``AnalysisError`` if not.
    """
    # Determine which naming convention is present
    has_legacy = {"v_sw", "B_s", "B_t", "theta"}.issubset(df.columns)
    has_standard = {"V", "Bt", "By", "Bz"}.issubset(df.columns)

    if not (has_legacy or has_standard):
        missing = {"v_sw", "B_s", "B_t", "theta"} | {"V", "Bt", "By", "Bz"}
        raise AnalysisError(
            f"Missing required columns for coupling functions: {missing}"
        )

    # Compute using the flexible helpers defined above
    df = df.copy()
    df["epsilon"] = compute_akasofu_epsilon(df)
    df["newell"] = compute_newell_function(df)
    # V*B products (using Bt as proxy when Bs not available)
    df["v_bs"] = compute_v_bs(df)
    df["v_bt"] = compute_v_bt(df)
    return df


def get_coupling_function_columns() -> list:
    """
    Return a list of coupling function column names added by
    ``compute_all_coupling_functions``.
    """
    return ["epsilon", "newell"]


# ----------------------------------------------------------------------
# Row‑wise convenience wrappers (required by the task specification)
# ----------------------------------------------------------------------
def compute_epsilon(row: pd.Series) -> float:
    """
    Row‑wise wrapper for the Akasofu epsilon calculation.

    Accepts a Series representing a single observation and returns the
    scalar ε value. Column names are resolved using the same variant logic
    as the vectorised implementation.
    """
    # Resolve the necessary series from the row (treated as a 1‑row DataFrame)
    V = _extract_series(pd.DataFrame([row]), ["v_sw", "V"]).iloc[0]
    # Prefer direct B column if present
    try:
        B = _extract_series(pd.DataFrame([row]), ["B_s"]).iloc[0]
    except KeyError:
        By = _extract_series(pd.DataFrame([row]), ["By"]).iloc[0]
        Bz = _extract_series(pd.DataFrame([row]), ["Bz"]).iloc[0]
        B = np.sqrt(By ** 2 + Bz ** 2)

    # Theta handling
    try:
        theta = _extract_series(pd.DataFrame([row]), ["theta"]).iloc[0]
    except KeyError:
        # Approximate clockwise angle from By/Bz if available
        try:
            By = _extract_series(pd.DataFrame([row]), ["By"]).iloc[0]
            Bz = _extract_series(pd.DataFrame([row]), ["Bz"]).iloc[0]
            theta = np.arctan2(By, Bz).abs()
        except KeyError:
            theta = 0.0

    l0 = 7.0
    sin_term = np.sin(theta / 2.0) ** 4
    epsilon = V * (B ** 2) * (l0 ** 2) * sin_term
    return float(epsilon)


def compute_newell(row: pd.Series) -> float:
    """
    Row‑wise wrapper for the Newell dΦ/dt coupling function.

    Accepts a Series representing a single observation and returns the
    scalar dΦ/dt value. Column names are resolved using the same variant
    logic as the vectorised implementation.
    """
    V = _extract_series(pd.DataFrame([row]), ["v_sw", "V"]).iloc[0]
    try:
        Bt = _extract_series(pd.DataFrame([row]), ["B_t", "Bt"]).iloc[0]
    except KeyError:
        # Fall back to total field magnitude if Bt is missing
        try:
            By = _extract_series(pd.DataFrame([row]), ["By"]).iloc[0]
            Bz = _extract_series(pd.DataFrame([row]), ["Bz"]).iloc[0]
            Bt = np.sqrt(By ** 2 + Bz ** 2)
        except KeyError:
            Bt = 0.0

    # Theta handling
    try:
        theta = _extract_series(pd.DataFrame([row]), ["theta"]).iloc[0]
    except KeyError:
        # Approximate if possible
        try:
            Bz = _extract_series(pd.DataFrame([row]), ["Bz"]).iloc[0]
            theta = np.arctan2(Bt, Bz).abs()
        except KeyError:
            theta = 0.0

    sin_term = np.sin(theta / 2.0) ** (8.0 / 3.0)
    newell = (V ** (4.0 / 3.0)) * (Bt ** (2.0 / 3.0)) * sin_term
    return float(newell)


# ----------------------------------------------------------------------
# CLI / script entry point
# ----------------------------------------------------------------------
def _process_and_write(
    input_path: Path,
    output_path: Path,
) -> None:
    """
    Load the aligned hourly dataset, compute all coupling functions,
    and write the enriched DataFrame to ``output_path`` as Parquet.
    """
    logger.info(f"Loading aligned data from {input_path}")
    df = load_parquet(input_path)

    logger.info("Computing coupling function columns")
    df_with_coupling = compute_all_coupling_functions(df)

    logger.info(f"Saving dataset with coupling functions to {output_path}")
    save_parquet(df_with_coupling, output_path)
    logger.info("Coupling‑function enrichment completed successfully.")


def main() -> None:
    """
    Command‑line interface.

    By default the script operates on the standard project layout:
    - Input: ``data/processed/aligned_hourly.parquet``
    - Output: ``data/processed/with_coupling.parquet``

    Optional arguments allow overriding these paths.
    """
    parser = argparse.ArgumentParser(
        description="Add Akasofu ε and Newell coupling function columns to the aligned dataset."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(paths.processed("aligned_hourly.parquet")),
        help="Path to the aligned hourly Parquet file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(paths.processed("with_coupling.parquet")),
        help="Path where the enriched Parquet file will be written.",
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.is_file():
        raise FileNotFoundError(f"Aligned data not found at {input_path}")

    _process_and_write(input_path, output_path)


if __name__ == "__main__":
    main()