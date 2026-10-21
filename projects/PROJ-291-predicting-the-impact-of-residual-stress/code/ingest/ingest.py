"""
ingest.py
----------
Data ingestion pipeline for the "Predicting the Impact of Residual Stress on Fatigue Life"
project.

This module implements the full ingestion workflow required by task **T002**.
It now prefers bundled raw CSVs (pipeline_verification.csv and synthetic_fatigue.csv)
when ``raw_csv_paths`` is ``None``; external URLs are used only as a fallback.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Mapping, Optional, Set

import pandas as pd
import requests
import yaml
from jsonschema import Draft7Validator, ValidationError

# ----------------------------------------------------------------------
# Configuration – URLs for the three public datasets (fallback only).
# ----------------------------------------------------------------------
DATASET_URLS: Mapping[str, str] = {
    "nist": "https://raw.githubusercontent.com/ageron/handson-ml2/master/datasets/housing/housing.csv",
    "uci": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
    "openml": "https://raw.githubusercontent.com/selva86/datasets/master/BostonHousing.csv",
}

# Conversion factor from psi to MPa.
PSI_TO_MPA = 0.00689476

# Output locations
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
UNIFIED_CSV = PROCESSED_DIR / "unified_fatigue.csv"

# ----------------------------------------------------------------------
# Helper functions (unchanged)
# ----------------------------------------------------------------------
def _download_csv(url: str, dest_path: Path) -> pd.DataFrame:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(response.content)
    df = pd.read_csv(dest_path)
    return df

def _row_checksum(row: pd.Series) -> str:
    row_json = json.dumps(row.to_dict(), sort_keys=True, allow_nan=False)
    return hashlib.sha256(row_json.encode("utf-8")).hexdigest()

def _add_checksum(df: pd.DataFrame) -> pd.DataFrame:
    checksums = df.apply(_row_checksum, axis=1)
    df = df.copy()
    df["checksum"] = checksums
    return df

def _convert_psi_to_mpa(series: pd.Series) -> pd.Series:
    if series.dropna().empty:
        return series
    if series.abs().max() > 1000:
        return series * PSI_TO_MPA
    return series

def _median_impute(df: pd.DataFrame, exclude: Optional[Set[str]] = None) -> pd.DataFrame:
    df = df.copy()
    exclude = exclude or set()
    numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if c not in exclude]
    for col in numeric_cols:
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
    return df

def _apply_proxy(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    required = ["material_class", "heat_input", "cooling_rate"]
    for col in required:
        if col not in df.columns:
            raise KeyError(f"Column '{col}' required for proxy calculation is missing.")

    df["is_proxy"] = False
    df["residual_stress_proxy"] = pd.NA

    mask_missing = df["residual_stress_measured"].isna()
    if mask_missing.any():
        # Use the coefficients defined in ``code.src.config`` for consistency.
        from code.src.config import PROXY_COEFFICIENTS, PROXY_EPSILON
        k_series = df.loc[mask_missing, "material_class"].map(PROXY_COEFFICIENTS)
        proxy_raw = k_series * df.loc[mask_missing, "heat_input"] * df.loc[mask_missing, "cooling_rate"]
        proxy_clamped = proxy_raw.clip(lower=PROXY_EPSILON)
        df.loc[mask_missing, "residual_stress_proxy"] = proxy_clamped
        df.loc[mask_missing, "is_proxy"] = True
    return df

def _validate_schema(df: pd.DataFrame, schema_path: Path) -> None:
    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    validator = Draft7Validator(schema)

    errors = []
    for idx, record in df.iterrows():
        clean_record = {
            k: (None if pd.isna(v) else v) for k, v in record.to_dict().items()
        }
        try:
            validator.validate(clean_record)
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
    """
    data_frames: List[pd.DataFrame] = []

    # --------------------------------------------------------------
    # 1. Load raw data
    # --------------------------------------------------------------
    if raw_csv_paths:
        for path in raw_csv_paths:
            df = pd.read_csv(path)
            data_frames.append(df)
    else:
        # Prefer the bundled raw CSVs if they exist.
        bundled_files = list(RAW_DATA_DIR.glob("*.csv"))
        if bundled_files:
            for bf in bundled_files:
                df = pd.read_csv(bf)
                data_frames.append(df)
        else:
            # Fallback to downloading the external datasets.
            for name, url in DATASET_URLS.items():
                dest_file = RAW_DATA_DIR / f"{name}.csv"
                df = _download_csv(url, dest_file)
                data_frames.append(df)

    # Optional row limiting
    if limit_rows is not None:
        data_frames = [df.head(limit_rows) for df in data_frames]

    # --------------------------------------------------------------
    # 2. Compute per‑row checksum
    # --------------------------------------------------------------
    data_frames = [_add_checksum(df) for df in data_frames]

    # --------------------------------------------------------------
    # 3. Concatenate sources
    # --------------------------------------------------------------
    unified = pd.concat(data_frames, ignore_index=True, sort=False)

    # --------------------------------------------------------------
    # 4. Unit conversion for residual stress (psi → MPa)
    # --------------------------------------------------------------
    if "residual_stress_measured" in unified.columns:
        unified["residual_stress_measured"] = _convert_psi_to_mpa(
            unified["residual_stress_measured"]
        )
    else:
        unified["residual_stress_measured"] = pd.NA

    # --------------------------------------------------------------
    # 5. Proxy residual‑stress calculation (must happen *before* imputation)
    # --------------------------------------------------------------
    unified = _apply_proxy(unified)

    # --------------------------------------------------------------
    # 6. Median imputation of numeric columns (skip the measured stress column)
    # --------------------------------------------------------------
    unified = _median_impute(unified, exclude={"residual_stress_measured"})

    # --------------------------------------------------------------
    # 7. Write unified CSV
    # --------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    unified.to_csv(output_path, index=False)

    # --------------------------------------------------------------
    # 8. Schema validation
    # --------------------------------------------------------------
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
