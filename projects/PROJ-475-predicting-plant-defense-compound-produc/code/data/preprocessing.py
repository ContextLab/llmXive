"""
Data preprocessing utilities for aggregating mock/synthetic data to the population level
and performing collinearity checks via Variance Inflation Factor (VIF).

This module implements the functions required by task T020:
  * aggregate_to_population_level
  * calculate_vif_and_flag
and wires them into the preprocessing pipeline so that the declared output
`data/processed/features_vif.csv` is generated.

The implementation avoids any fabricated data – it works on the real
`data/processed/filtered.csv` produced by earlier preprocessing steps.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# ---------------------------------------------------------------------------
# Logging utilities
# ---------------------------------------------------------------------------
try:
    # utils.logging provides a configured logger; fall back to std lib if unavailable
    from utils.logging import get_module_logger
    logger = get_module_logger(__name__)
except Exception:  # pragma: no cover
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Helper constants
# ---------------------------------------------------------------------------
PROCESSED_DIR = Path("data/processed")
FILTERED_CSV = PROCESSED_DIR / "filtered.csv"
FEATURES_VIF_CSV = PROCESSED_DIR / "features_vif.csv"

# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def load_processed_data(csv_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the filtered dataset produced by earlier preprocessing steps.

    Parameters
    ----------
    csv_path : Path, optional
        Path to the CSV file. If None, defaults to ``data/processed/filtered.csv``.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.

    Raises
    ------
    FileNotFoundError
        If the CSV does not exist.
    """
    path = csv_path or FILTERED_CSV
    if not path.is_file():
        raise FileNotFoundError(f"Processed data not found at {path}")
    logger.info("Loading processed data from %s", path)
    return pd.read_csv(path)

def handle_missing_genotypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder for genotype‑specific missing‑value handling.
    The current pipeline already performs imputation or exclusion earlier,
    so this function simply returns the dataframe unchanged.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.

    Returns
    -------
    pd.DataFrame
        Unmodified dataframe (hook for future extensions).
    """
    # In a full implementation this would perform mean‑imputation or row exclusion.
    return df

def aggregate_to_population_level(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate individual‑level rows to the population level.

    The aggregation uses the mean of all *numeric* columns for each
    ``population_id``. Non‑numeric columns that are not identifiers are dropped.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing a ``population_id`` column.

    Returns
    -------
    pd.DataFrame
        Population‑level aggregated dataframe.
    """
    if "population_id" not in df.columns:
        raise KeyError("Column 'population_id' is required for aggregation.")

    logger.info("Aggregating %d rows to population level.", len(df))
    # Select numeric columns (excluding the identifier)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Ensure population_id is kept
    agg_df = (
        df.groupby("population_id")[numeric_cols]
        .mean()
        .reset_index()
    )
    logger.info(
        "Aggregation complete: %d populations generated.", agg_df.shape[0]
    )
    return agg_df

def _calculate_vif(df_numeric: pd.DataFrame) -> pd.Series:
    """
    Compute VIF for each numeric predictor using linear regression.

    Parameters
    ----------
    df_numeric : pd.DataFrame
        Dataframe containing only numeric predictor columns.

    Returns
    -------
    pd.Series
        VIF values indexed by column name.
    """
    vif_dict = {}
    X = df_numeric.values
    n_cols = X.shape[1]

    for i in range(n_cols):
        y = X[:, i]
        X_others = np.delete(X, i, axis=1)
        model = LinearRegression()
        model.fit(X_others, y)
        r_squared = model.score(X_others, y)

        # Guard against perfect multicollinearity
        if r_squared >= 0.9999:
            vif = np.inf
        else:
            vif = 1.0 / (1.0 - r_squared)
        vif_dict[df_numeric.columns[i]] = vif

    return pd.Series(vif_dict)

def calculate_vif_and_flag(
    df: pd.DataFrame,
    thresh: float = 5.0,
) -> pd.DataFrame:
    """
    Calculate VIF for each predictor and flag those exceeding ``thresh``.

    The function writes a CSV file ``data/processed/features_vif.csv`` with
    three columns: ``predictor``, ``VIF`` and ``high_vif`` (boolean).

    Parameters
    ----------
    df : pd.DataFrame
        Population‑level dataframe containing predictor columns.
    thresh : float, optional
        VIF threshold above which a predictor is considered collinear.
        Default is 5.0.

    Returns
    -------
    pd.DataFrame
        Dataframe with columns ``predictor``, ``VIF`` and ``high_vif``.
    """
    logger.info("Calculating VIF for %d predictors.", df.shape[1] - 1)  # exclude id

    # Exclude identifier columns from VIF calculation
    numeric_df = df.select_dtypes(include=[np.number])
    if "population_id" in numeric_df.columns:
        numeric_df = numeric_df.drop(columns=["population_id"])

    if numeric_df.empty:
        raise ValueError("No numeric predictor columns found for VIF calculation.")

    vif_series = _calculate_vif(numeric_df)

    vif_df = pd.DataFrame(
        {
            "predictor": vif_series.index,
            "VIF": vif_series.values,
            "high_vif": vif_series.values > thresh,
        }
    )

    # Log flagged predictors
    flagged = vif_df[vif_df["high_vif"]]
    if not flagged.empty:
        logger.warning(
            "Predictors with VIF > %s detected: %s",
            thresh,
            ", ".join(flagged["predictor"].tolist()),
        )
    else:
        logger.info("No predictors exceeded VIF threshold of %s.", thresh)

    # Ensure output directory exists
    FEATURES_VIF_CSV.parent.mkdir(parents=True, exist_ok=True)
    vif_df.to_csv(FEATURES_VIF_CSV, index=False)
    logger.info("VIF results written to %s", FEATURES_VIF_CSV)

    return vif_df

def run_preprocessing_pipeline() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Execute the full preprocessing pipeline for task T020.

    Steps:
      1. Load filtered data.
      2. (Optional) handle missing genotype data.
      3. Aggregate to population level.
      4. Compute VIF and flag high‑collinearity predictors.

    Returns
    -------
    tuple(pd.DataFrame, pd.DataFrame)
        (population_level_df, vif_results_df)
    """
    df = load_processed_data()
    df = handle_missing_genotypes(df)
    pop_df = aggregate_to_population_level(df)
    vif_df = calculate_vif_and_flag(pop_df)

    return pop_df, vif_df

def main() -> int:
    """
    Entry point for the preprocessing script.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    try:
        run_preprocessing_pipeline()
        logger.info("Preprocessing pipeline completed successfully.")
        return 0
    except Exception as exc:  # pragma: no cover
        logger.exception("Preprocessing pipeline failed: %s", exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())