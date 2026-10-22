"""
code/src/build_features.py
--------------------------
Constructs the four feature sets required for downstream modeling:

* Feature Set A – process‑parameter columns only, **restricted to the
  balanced subset where measured residual stress is available**.
* Feature Set B (balanced) – process parameters + measured residual stress,
  using the same balanced subset as Feature Set A.
* Feature Set B‑full – process parameters + residual‑stress column that
  prefers measured values and falls back to the proxy for the full dataset.
* Feature Set C – process parameters + material‑property attributes +
  the proxy stress column (full dataset).

All numeric features are standardised (zero mean, unit variance) using a
``sklearn.preprocessing.StandardScaler``.  The fitted scalers are persisted
to ``data/processed`` so that later stages (training, inference) can reuse
them.
"""

import json
from pathlib import Path
from typing import Dict

import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_unified_dataset(unified_path: Path = None) -> pd.DataFrame:
    """Load the unified fatigue CSV produced by the ingestion step."""
    if unified_path is None:
        unified_path = paths.processed("unified_fatigue.csv")
    if not unified_path.is_file():
        raise FileNotFoundError(
            f"Unified dataset not found at {unified_path}. "
            "Run the ingestion pipeline before building features."
        )
    df = pd.read_csv(unified_path)
    return df

def _select_process_columns(df: pd.DataFrame) -> list:
    """
    Return a list of column names that are considered *process parameters*.

    The project schema defines the following columns as process‑related:
    ``heat_input``, ``cooling_rate`` and ``other_process_params``.
    Any additional columns that are not explicitly recognised as material
    properties, stress, target or metadata are ignored for simplicity.
    """
    candidate = ["heat_input", "cooling_rate", "other_process_params"]
    return [c for c in candidate if c in df.columns]

def _select_material_property_columns(df: pd.DataFrame) -> list:
    """Columns that describe material‑property attributes."""
    candidate = ["elastic_modulus", "yield_strength"]
    return [c for c in candidate if c in df.columns]

def _standardise(df: pd.DataFrame) -> (pd.DataFrame, StandardScaler):
    """
    Standardise *numeric* columns of ``df`` using a fresh ``StandardScaler``.
    Non‑numeric columns are left untouched.  Returns the transformed
    DataFrame and the fitted scaler.
    """
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    scaler = StandardScaler()
    if numeric_cols:
        df_loc = df.loc[:, numeric_cols]
        scaled = scaler.fit_transform(df_loc)
        df.loc[:, numeric_cols] = scaled
    return df, scaler

def _save_scaler(scaler: StandardScaler, name: str) -> None:
    """Persist a scaler under ``data/processed/scaler_<name>.pkl``."""
    out_path: Path = paths.processed(f"scaler_{name}.pkl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, out_path)
    log.info("Scaler %s written to %s", name, out_path)

def _write_feature_set(df: pd.DataFrame, name: str) -> None:
    """Write a feature set CSV to ``data/processed/feature_set_<name>.csv``."""
    out_path: Path = paths.processed(f"feature_set_{name}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    log.info("Feature set %s written to %s", name, out_path)

# ----------------------------------------------------------------------
# Core builder
# ----------------------------------------------------------------------
def build_feature_sets(unified_path: Path = None) -> Dict[str, pd.DataFrame]:
    """
    Build and persist all four feature sets.

    Returns
    -------
    dict
        Mapping from feature‑set name (``A``, ``B_balanced``, ``B_full``,
        ``C``) to the corresponding processed ``DataFrame``.
    """
    df = _load_unified_dataset(unified_path)

    # ------------------------------------------------------------------
    # Identify the balanced subset (rows where measured stress is present)
    # ------------------------------------------------------------------
    if "is_proxy" not in df.columns:
        raise KeyError("Column 'is_proxy' missing – cannot build balanced sets.")
    mask_measured = ~df["is_proxy"].astype(bool)

    # ------------------------------------------------------------------
    # 1. Feature Set A – process parameters only, on the balanced subset
    # ------------------------------------------------------------------
    proc_cols = _select_process_columns(df)
    if not proc_cols:
        raise ValueError("No process‑parameter columns found in the dataset.")
    df_balanced = df.loc[mask_measured].reset_index(drop=True)
    X_A = df_balanced[proc_cols].copy()
    X_A, scaler_A = _standardise(X_A)
    _save_scaler(scaler_A, "A")
    _write_feature_set(X_A, "A")

    # ------------------------------------------------------------------
    # 2. Feature Set B (balanced) – process + measured stress, rows where
    #    ``is_proxy`` is False.
    # ------------------------------------------------------------------
    b_balanced_cols = proc_cols + ["residual_stress_measured"]
    X_B_balanced = df_balanced[b_balanced_cols].copy()
    X_B_balanced, scaler_B = _standardise(X_B_balanced)
    _save_scaler(scaler_B, "B_balanced")
    _write_feature_set(X_B_balanced, "B_balanced")

    # ------------------------------------------------------------------
    # 3. Feature Set B‑full – process + stress (measured when present,
    #    otherwise proxy) on the full dataset.
    # ------------------------------------------------------------------
    if "residual_stress_measured" not in df.columns or "residual_stress_proxy" not in df.columns:
        raise KeyError("Required stress columns missing for B‑full construction.")
    stress_full = df["residual_stress_measured"].copy()
    missing = stress_full.isna()
    stress_full.loc[missing] = df.loc[missing, "residual_stress_proxy"]
    X_B_full = df[proc_cols].copy()
    X_B_full["residual_stress"] = stress_full
    X_B_full, scaler_B_full = _standardise(X_B_full)
    _save_scaler(scaler_B_full, "B_full")
    _write_feature_set(X_B_full, "B_full")

    # ------------------------------------------------------------------
    # 4. Feature Set C – process + material properties + proxy (full dataset)
    # ------------------------------------------------------------------
    mat_prop_cols = _select_material_property_columns(df)
    if not mat_prop_cols:
        raise ValueError("No material‑property columns found for Feature Set C.")
    if "residual_stress_proxy" not in df.columns:
        raise KeyError("Column 'residual_stress_proxy' missing for Feature Set C.")
    X_C = df[proc_cols + mat_prop_cols + ["residual_stress_proxy"]].copy()
    X_C, scaler_C = _standardise(X_C)
    _save_scaler(scaler_C, "C")
    _write_feature_set(X_C, "C")

    log.info("All feature sets built successfully.")
    return {
        "A": X_A,
        "B_balanced": X_B_balanced,
        "B_full": X_B_full,
        "C": X_C,
    }

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv=None) -> None:
    """
    CLI entry point – simply builds the feature sets using the default
    unified‑dataset location.
    """
    build_feature_sets()
    log.info("Feature‑set construction completed.")

if __name__ == "__main__":
    main()
