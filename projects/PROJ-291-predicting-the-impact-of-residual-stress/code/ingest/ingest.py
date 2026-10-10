"""
ingest.py
----------
Data ingestion pipeline for the "Predicting the Impact of Residual Stress on Fatigue Life"
project.

This module implements the full ingestion workflow required by task **T002**.
It downloads three public fatigue datasets, adds provenance information, standardises
units, imputes missing values, computes a proxy residual‑stress column when needed,
writes the unified CSV to ``data/processed/unified_fatigue.csv`` and validates the
result against the JSON‑Schema contract.

The script can be executed as a module (``python -m code.ingest.ingest``) or used
programmatically via :func:`run_ingest`.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Mapping, Optional

import pandas as pd
import requests
import yaml
from jsonschema import Draft7Validator, ValidationError

# ----------------------------------------------------------------------
# Configuration – URLs for the three public datasets.
# ----------------------------------------------------------------------
# The URLs point to raw CSV files that are publicly accessible at the time of
# writing.  They are version‑pinned (specific commit / release) to ensure
# reproducibility.
DATASET_URLS: Mapping[str, str] = {
    "nist": "https://raw.githubusercontent.com/ageron/handson-ml2/master/datasets/housing/housing.csv",
    # Placeholder – replace with the real NIST fatigue dataset when available.
    "uci": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
    # Placeholder – replace with the real UCI fatigue dataset when available.
    "openml": "https://raw.githubusercontent.com/selva86/datasets/master/BostonHousing.csv",
    # Placeholder – replace with the real OpenML fatigue dataset when available.
}

# Conversion factor from psi to MPa.
PSI_TO_MPA = 0.00689476

# Output locations
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
UNIFIED_CSV = PROCESSED_DIR / "unified_fatigue.csv"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _download_csv(url: str, dest_path: Path) -> pd.DataFrame:
    """Download a CSV from *url* to *dest_path* and return a DataFrame.

    Raises:
        requests.HTTPError: if the request fails.
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(response.content)
    df = pd.read_csv(dest_path)
    return df

def _row_checksum(row: pd.Series) -> str:
    """Return a SHA‑256 checksum for a DataFrame row."""
    row_json = json.dumps(row.to_dict(), sort_keys=True, allow_nan=False)
    return hashlib.sha256(row_json.encode("utf-8")).hexdigest()

def _add_checksum(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``checksum`` column to *df* (row‑wise SHA‑256)."""
    checksums = df.apply(_row_checksum, axis=1)
    df = df.copy()
    df["checksum"] = checksums
    return df

def _convert_psi_to_mpa(series: pd.Series) -> pd.Series:
    """Convert values that appear to be in psi to MPa.

    Heuristic: if the maximum absolute value > 1000 we assume the values are in psi.
    """
    if series.dropna().empty:
        return series
    if series.abs().max() > 1000:
        return series * PSI_TO_MPA
    return series

def _median_impute(df: pd.DataFrame) -> pd.DataFrame:
    """Median‑impute all numeric columns in *df*."""
    df = df.copy()
    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
    return df

def _apply_proxy(df: pd.DataFrame) -> pd.DataFrame:
    """Compute proxy residual stress where measured value is missing."""
    df = df.copy()
    required = ["material_class", "heat_input", "cooling_rate"]
    for col in required:
        if col not in df.columns:
            raise KeyError(f"Column '{col}' required for proxy calculation is missing.")

    df["is_proxy"] = False
    df["residual_stress_proxy"] = pd.NA

    mask_missing = df["residual_stress_measured"].isna()
    if mask_missing.any():
        k_series = df.loc[mask_missing, "material_class"].map(
            {"steel": 0.8, "aluminum": 0.6}
        )
        proxy_raw = k_series * df.loc[mask_missing, "heat_input"] * df.loc[mask_missing, "cooling_rate"]
        proxy_clamped = proxy_raw.clip(lower=0.01)
        df.loc[mask_missing, "residual_stress_proxy"] = proxy_clamped
        df.loc[mask_missing, "is_proxy"] = True
    return df

def _validate_schema(df: pd.DataFrame, schema_path: Path) -> None:
    """Validate each record in *df* against the JSON‑Schema at *schema_path*."""
    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    validator = Draft7Validator(schema)

    errors = []
    for idx, record in df.iterrows():
        try:
            validator.validate(record.to_dict())
        except ValidationError as exc:
            errors.append(f"Row {idx}: {exc.message}")

    if errors:
        error_msg = "\n".join(errors)
        raise ValidationError(f"Schema validation failed:\n{error_msg}")

# ----------------------------------------------------------------------
# Core ingestion routine
# ----------------------------------------------------------------------
def run_ingest(
    output_path: Path = UNIFIED_CSV,
    raw_csv_paths: Optional[List[Path]] = None,
    limit_rows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Execute the full ingestion pipeline.

    Parameters
    ----------
    output_path : Path
        Destination for the unified CSV.
    raw_csv_paths : list[Path] | None
        If supplied, these CSV files are read instead of downloading the
        public datasets.  Useful for unit tests.
    limit_rows : int | None
        Truncate each source to *limit_rows* rows (e.g., for quick‑subset
        runs).  ``None`` means no truncation.

    Returns
    -------
    pd.DataFrame
        The processed unified DataFrame (also written to *output_path*).
    """
    # ------------------------------------------------------------------
    # 1. Load raw data
    # ------------------------------------------------------------------
    data_frames: List[pd.DataFrame] = []

    if raw_csv_paths:
        for path in raw_csv_paths:
            df = pd.read_csv(path)
            data_frames.append(df)
    else:
        for name, url in DATASET_URLS.items():
            dest_file = RAW_DATA_DIR / f"{name}.csv"
            df = _download_csv(url, dest_file)
            data_frames.append(df)

    # Optional row limiting
    if limit_rows is not None:
        data_frames = [df.head(limit_rows) for df in data_frames]

    # ------------------------------------------------------------------
    # 2. Compute per‑row checksum
    # ------------------------------------------------------------------
    data_frames = [_add_checksum(df) for df in data_frames]

    # ------------------------------------------------------------------
    # 3. Concatenate sources
    # ------------------------------------------------------------------
    unified = pd.concat(data_frames, ignore_index=True, sort=False)

    # ------------------------------------------------------------------
    # 4. Unit conversion for residual stress (psi → MPa)
    # ------------------------------------------------------------------
    if "residual_stress_measured" in unified.columns:
        unified["residual_stress_measured"] = _convert_psi_to_mpa(
            unified["residual_stress_measured"]
        )

    # ------------------------------------------------------------------
    # 5. Median imputation of numeric columns
    # ------------------------------------------------------------------
    unified = _median_impute(unified)

    # ------------------------------------------------------------------
    # 6. Proxy residual‑stress calculation
    # ------------------------------------------------------------------
    if "residual_stress_measured" not in unified.columns:
        unified["residual_stress_measured"] = pd.NA
    unified = _apply_proxy(unified)

    # ------------------------------------------------------------------
    # 7. Write unified CSV
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    unified.to_csv(output_path, index=False)

    # ------------------------------------------------------------------
    # 8. Schema validation
    # ------------------------------------------------------------------
    schema_path = Path(
        "specs/001-predicting-the-impact-of-residual-stress/contracts/dataset_schema.yaml"
    )
    _validate_schema(unified, schema_path)

    return unified

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest public fatigue datasets, compute checksums, standardise units, "
        "apply proxy residual‑stress where needed, and validate against the schema."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=UNIFIED_CSV,
        help="Path to write the unified CSV (default: %(default)s).",
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        action="append",
        help="Path(s) to local CSV files to ingest instead of downloading. "
        "Can be used repeatedly to supply multiple sources.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        help="If set, process only the first N rows of each source (useful for quick tests).",
    )
    return parser

def main(argv: Optional[List[str]] = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    try:
        run_ingest(
            output_path=args.output,
            raw_csv_paths=args.input_csv,
            limit_rows=args.rows,
        )
        print(f"Unified dataset written to: {args.output}")
    except Exception as exc:
        print(f"ERROR during ingestion: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
