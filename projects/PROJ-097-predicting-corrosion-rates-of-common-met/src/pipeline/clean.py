"""Cleaning, validation & unit harmonisation (Task T002).

This module provides a reusable ``clean_dataset`` function that can be
imported by other scripts (e.g. the training pipeline) and a CLI entry
point for manual execution.

The implementation mirrors the logic used in ``src.pipeline.ingest`` but
is kept separate so that downstream stages can invoke cleaning directly
without re‑downloading the raw file.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

import pandas as pd
from llmxive_toolkit import get_logger

log = get_logger(__name__)

# Mapping from the canonical pipeline variable names to the source column
# names expected in the raw CSV.  The ingest script uses the same mapping,
# so this function works for any dataset that follows that convention.
REQUIRED_MAP = {
    "ph": "ph",
    "salinity": "salinity",
    "temperature": "temperature",
    "composition": "composition",
    "corrosion_rate": "corrosion_rate_mm_per_year",
    "source_id": "source_id",
}

def _verify_required_columns(df: pd.DataFrame, source: str) -> None:
    """Abort with ``RuntimeError`` if a required column is missing."""
    for canonical in REQUIRED_MAP:
        source_col = REQUIRED_MAP[canonical]
        if source_col not in df.columns:
            raise RuntimeError(f"Error: MISSING_VARIABLE {canonical} in {source}")

def _harmonize_corrosion_rate(series: pd.Series) -> pd.Series:
    """Convert corrosion‑rate values to mm / year (identity conversion)."""
    return pd.to_numeric(series, errors="coerce")

def _impute_missing(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Impute missing values (median for numeric, mode for categorical)."""
    for col in df.columns:
        if col == target_col:
            continue
        if df[col].isna().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                median = df[col].median()
                df[col].fillna(median, inplace=True)
            else:
                mode = df[col].mode().iloc[0]
                df[col].fillna(mode, inplace=True)
    return df

def _standardize_numeric(df: pd.DataFrame, numeric_cols: Sequence[str]) -> pd.DataFrame:
    """Z‑score standardise the listed numeric columns."""
    for col in numeric_cols:
        mean = df[col].mean()
        std = df[col].std()
        if std == 0:
            df[col] = 0.0
        else:
            df[col] = (df[col] - mean) / std
    return df

def _one_hot_encode_composition(df: pd.DataFrame) -> pd.DataFrame:
    """One‑hot encode ``composition`` while preserving the original label."""
    comp = df["composition"]
    dummies = pd.get_dummies(comp, prefix="composition")
    df = df.drop(columns=["composition"]).join(dummies)
    df["composition"] = comp
    return df

def clean_dataset(raw_path: str, cleaned_path: str) -> None:
    """Read *raw_path*, apply the cleaning pipeline, and write to *cleaned_path*."""
    df = pd.read_csv(raw_path)

    # Verify required columns.
    _verify_required_columns(df, source=raw_path)

    # Add a unique record identifier.
    df.insert(0, "record_id", [str(uuid.uuid4()) for _ in range(len(df))])

    # Optional column handling.
    if "crystal_structure" not in df.columns:
        log.warning("Optional column 'crystal_structure' not found; proceeding without it.")

    # Harmonise corrosion‑rate units.
    df["corrosion_rate"] = _harmonize_corrosion_rate(df["corrosion_rate"])

    # Impute missing values (excluding the target).
    df = _impute_missing(df, target_col="corrosion_rate")

    # Standardise numeric predictors.
    df = _standardize_numeric(df, numeric_cols=["ph", "salinity", "temperature"])

    # One‑hot encode composition.
    df = _one_hot_encode_composition(df)

    # Rename target column to match the schema.
    df.rename(columns={"corrosion_rate": "corrosion_rate_mm_per_year"}, inplace=True)

    # Write the cleaned CSV.
    pd.DataFrame(df).to_csv(cleaned_path, index=False)
    log.info("Cleaned dataset written to %s", cleaned_path)

def main(argv: list[str] | None = None) -> int:
    """CLI entry point: ``python -m src.pipeline.clean <raw> <cleaned>``."""
    import argparse
    parser = argparse.ArgumentParser(description="Clean the raw corrosion dataset.")
    parser.add_argument("raw_path", help="Path to the raw CSV file.")
    parser.add_argument("cleaned_path", help="Destination path for the cleaned CSV.")
    args = parser.parse_args(argv)

    try:
        clean_dataset(args.raw_path, args.cleaned_path)
        return 0
    except Exception as exc:  # pragma: no cover
        log.exception("Cleaning failed: %s", exc)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())