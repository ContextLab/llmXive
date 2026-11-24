"""Compute Variance Inflation Factor (VIF) diagnostics for base predictors.

This script reads the cleaned dataset produced by the ingestion step,
selects the base predictor columns (numeric environmental variables and the
one‑hot encoded composition columns), computes the VIF for each predictor,
writes the results to ``data/results/vif_diagnostics.json`` and logs a
warning for any VIF value exceeding the threshold of 5.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict

import pandas as pd
import statsmodels.api as sm

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

VIF_WARNING_THRESHOLD = 5.0

def _select_base_predictors(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame containing only the base predictor columns.

    Base predictors are:
    - Numeric environmental variables: ``ph``, ``salinity``, ``temperature``.
    - One‑hot encoded composition columns (prefixed with ``composition_``).
    The target column ``corrosion_rate`` and the grouping column ``source_id``
    are excluded.
    """
    target_col = "corrosion_rate"
    exclude = {target_col, "source_id"}
    # Identify one‑hot composition columns by prefix.
    composition_prefix = "composition_"
    base_cols = [
        col
        for col in df.columns
        if col not in exclude
        and (
            col in ("ph", "salinity", "temperature")
            or col.startswith(composition_prefix)
        )
    ]
    if not base_cols:
        raise RuntimeError("No base predictor columns found for VIF computation.")
    return df[base_cols]

def compute_vif(df: pd.DataFrame) -> Dict[str, float]:
    """Compute VIF for each column in *df*.

    Returns a dictionary mapping column name → VIF value.
    """
    vif_dict: Dict[str, float] = {}
    # Ensure there are no missing values; VIF cannot handle NaNs.
    if df.isnull().any().any():
        raise RuntimeError("VIF computation requires a DataFrame without missing values.")
    for col in df.columns:
        y = df[col]
        X = df.drop(columns=[col])
        # Add a constant term for the OLS regression.
        X_const = sm.add_constant(X, has_constant="add")
        model = sm.OLS(y, X_const).fit()
        r2 = model.rsquared
        # Guard against perfect collinearity.
        if r2 >= 1.0:
            vif = float("inf")
        else:
            vif = 1.0 / (1.0 - r2)
        vif_dict[col] = vif
        if vif > VIF_WARNING_THRESHOLD:
            log.warning("VIF for %s is %.2f (> %.1f)", col, vif, VIF_WARNING_THRESHOLD)
    return vif_dict

def main(argv: list[str] | None = None) -> int:
    """Entry point for ``python -m src.pipeline.vif``."""
    # ``argv`` is ignored; the script always operates on the default paths.
    cleaned_path = paths.data("processed", "cleaned_dataset.csv")
    if not cleaned_path.is_file():
        log.error("Cleaned dataset not found at %s", cleaned_path)
        return 1

    df = pd.read_csv(cleaned_path)
    try:
        base_df = _select_base_predictors(df)
    except RuntimeError as exc:
        log.error(str(exc))
        return 1

    try:
        vif_results = compute_vif(base_df)
    except Exception as exc:
        log.exception("Failed to compute VIF: %s", exc)
        return 1

    out_path = paths.results("vif_diagnostics.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(vif_results, fh, indent=2, sort_keys=True)

    log.info("VIF diagnostics written to %s", out_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())