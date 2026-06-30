"""
Residual Analysis Module
------------------------

This script performs a residual analysis on the cleaned knot dataset to
identify knots whose hyperbolic volume deviates significantly from the
linear model relating volume to crossing number and braid index.

The original implementation relied on the project's reproducibility logger
which currently has an incompatible API (e.g. ``logger.debug`` expects a
different signature).  To keep this task self‑contained and avoid breaking
other parts of the pipeline, the implementation below:

* Loads the cleaned dataset directly (bypassing ``analysis._utils.load_cleaned_knots``)
* Uses plain ``logging`` for informational messages
* Provides the same public API as the original module (functions and ``main``)
* Writes the outlier information to ``data/processed/outlier_knots.json``

The output file is required by downstream tasks and the end‑to‑end
quick‑start script.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Data loading utilities
# ----------------------------------------------------------------------
_CLEANED_DATA_PATH = Path("data/processed/knots_cleaned.csv")


def _load_cleaned_knots() -> pd.DataFrame:
    """
    Load the cleaned knot dataset.

    Returns
    -------
    pd.DataFrame
        DataFrame containing at least the columns ``name``,
        ``crossing_number``, ``braid_index`` and ``volume``.
    """
    if not _CLEANED_DATA_PATH.is_file():
        raise FileNotFoundError(
            f"Cleaned knot data not found at {_CLEANED_DATA_PATH!s}"
        )
    df = pd.read_csv(_CLEANED_DATA_PATH, dtype=str)
    # Ensure required columns are present
    required = {"name", "crossing_number", "braid_index", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in cleaned data: {missing}")
    return df


# ----------------------------------------------------------------------
# Model fitting
# ----------------------------------------------------------------------
@dataclass
class LinearModelResult:
    """Result of the ordinary‑least‑squares linear regression."""

    intercept: float
    slope_crossing: float
    slope_braid: float
    r_squared: float


def fit_linear_model(df: pd.DataFrame) -> LinearModelResult:
    """
    Fit a linear model ``volume = a + b·crossing_number + c·braid_index``.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned knot data.

    Returns
    -------
    LinearModelResult
        Coefficients and R² of the fitted model.
    """
    # Convert to numeric, coercing errors to NaN
    df = df.copy()
    df["crossing_number"] = pd.to_numeric(df["crossing_number"], errors="coerce")
    df["braid_index"] = pd.to_numeric(df["braid_index"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

    # Drop rows with missing values in any of the three columns
    df = df.dropna(subset=["crossing_number", "braid_index", "volume"])

    X = df[["crossing_number", "braid_index"]].values
    y = df["volume"].values

    # Add intercept column
    X_design = np.column_stack((np.ones_like(y), X))

    # Ordinary least squares solution
    coeffs = np.linalg.lstsq(X_design, y, rcond=None)[0]
    intercept, slope_crossing, slope_braid = coeffs

    # Compute R²
    y_pred = X_design @ coeffs
    ss_res = ((y - y_pred) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan

    return LinearModelResult(
        intercept=intercept,
        slope_crossing=slope_crossing,
        slope_braid=slope_braid,
        r_squared=r_squared,
    )


# ----------------------------------------------------------------------
# Residual calculation
# ----------------------------------------------------------------------
@dataclass
class ResidualEntry:
    """One residual entry for a knot."""

    knot_id: str
    crossing_number: int
    braid_index: int
    observed_volume: float
    predicted_volume: float
    residual: float


def calculate_residuals(
    df: pd.DataFrame, model: LinearModelResult
) -> List[ResidualEntry]:
    """
    Compute residuals for each knot in ``df`` using ``model``.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned knot data.
    model : LinearModelResult
        Linear model fitted to the same data.

    Returns
    -------
    List[ResidualEntry]
    """
    df = df.copy()
    df["crossing_number"] = pd.to_numeric(df["crossing_number"], errors="coerce")
    df["braid_index"] = pd.to_numeric(df["braid_index"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

    # Drop rows with missing values to avoid NaNs in calculations
    df = df.dropna(subset=["crossing_number", "braid_index", "volume"])

    predicted = (
        model.intercept
        + model.slope_crossing * df["crossing_number"]
        + model.slope_braid * df["braid_index"]
    )
    residuals = df["volume"] - predicted

    entries: List[ResidualEntry] = []
    for idx, row in df.iterrows():
        entry = ResidualEntry(
            knot_id=row["name"],
            crossing_number=int(row["crossing_number"]),
            braid_index=int(row["braid_index"]),
            observed_volume=float(row["volume"]),
            predicted_volume=float(
                model.intercept
                + model.slope_crossing * row["crossing_number"]
                + model.slope_braid * row["braid_index"]
            ),
            residual=float(residuals.loc[idx]),
        )
        entries.append(entry)
    return entries


# ----------------------------------------------------------------------
# Outlier detection
# ----------------------------------------------------------------------
def identify_outliers(
    residuals: List[ResidualEntry], z_thresh: float = 2.5
) -> List[ResidualEntry]:
    """
    Identify outliers using a Z‑score threshold.

    Parameters
    ----------
    residuals : List[ResidualEntry]
        All residual entries.
    z_thresh : float, optional
        Z‑score magnitude above which a knot is considered an outlier.
        Default is 2.5.

    Returns
    -------
    List[ResidualEntry]
        Subset of ``residuals`` flagged as outliers.
    """
    if not residuals:
        return []

    residual_vals = np.array([r.residual for r in residuals])
    mean = residual_vals.mean()
    std = residual_vals.std(ddof=0)

    if std == 0:
        return []

    outliers = [
        r
        for r in residuals
        if abs((r.residual - mean) / std) >= z_thresh
    ]
    return outliers


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------
def save_outlier_knots_json(
    outliers: List[ResidualEntry], output_path: Path
) -> None:
    """
    Write outlier information to a JSON file.

    Parameters
    ----------
    outliers : List[ResidualEntry]
        Outlier entries to be saved.
    output_path : Path
        Destination file path. Parent directories are created as needed.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(o) for o in outliers], f, indent=2)


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the full residual‑analysis pipeline.

    The function:

    1. Loads the cleaned knot dataset.
    2. Fits the linear model.
    3. Calculates residuals.
    4. Detects outliers (Z‑score ≥ 2.5).
    5. Writes the outliers to ``data/processed/outlier_knots.json``.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logger = logging.getLogger(__name__)

    logger.info("Starting residual analysis")
    df = _load_cleaned_knots()
    model = fit_linear_model(df)
    logger.info(
        "Fitted linear model: intercept=%.4f, slope_crossing=%.4f, slope_braid=%.4f, R²=%.4f",
        model.intercept,
        model.slope_crossing,
        model.slope_braid,
        model.r_squared,
    )
    residuals = calculate_residuals(df, model)
    outliers = identify_outliers(residuals)
    out_path = Path("data/processed/outlier_knots.json")
    save_outlier_knots_json(outliers, out_path)
    logger.info(
        "Saved %d outlier knots to %s", len(outliers), out_path.as_posix()
    )


if __name__ == "__main__":
    main()