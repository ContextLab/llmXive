"""
ingest.py
----------
Core implementation of the data ingestion pipeline for the project.
It loads the two bundled raw CSV files (or any provided CSV/JSON files),
flattens nested JSON structures, standardises stress units, performs median
imputation, records missingness, computes a residual‑stress proxy, validates
the unified schema, and writes the resulting CSV and missing‑flags JSON.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Mapping, Optional, Set

import pandas as pd
import yaml
from jsonschema import Draft7Validator

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration constants (imported from the central config module)
# ----------------------------------------------------------------------
from code.src.config import PROXY_COEFFICIENTS, PROXY_EPSILON, SEED

# Default output location for the unified CSV
UNIFIED_CSV = paths.processed("unified_fatigue.csv")
MISSING_FLAGS_JSON = paths.processed("missing_flags.json")

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _download_csv(url: str, dest_path: Path) -> pd.DataFrame:
    """
    Placeholder for future remote CSV download. Currently unused because the
    pipeline works exclusively with the bundled raw files.
    """
    raise NotImplementedError("Remote download not supported in this repository.")

def _row_checksum(row: pd.Series) -> str:
    """
    Compute a deterministic SHA‑256 checksum for a single DataFrame row.
    The row is converted to a JSON string with sorted keys to guarantee
    reproducibility.
    """
    # Convert to a regular dict, handling NaNs as None for JSON compatibility
    row_dict = {
        k: (None if pd.isna(v) else v)
        for k, v in row.items()
    }
    json_bytes = json.dumps(row_dict, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(json_bytes).hexdigest()

def _add_checksum(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a ``checksum`` column to the DataFrame; each checksum is the SHA‑256
    hash of the corresponding row (pre‑checksum).
    """
    log.debug("Adding checksum column to %d rows", len(df))
    df = df.copy()
    df["checksum"] = df.apply(_row_checksum, axis=1)
    return df

def _convert_psi_to_mpa(series: pd.Series) -> pd.Series:
    """
    Convert a numeric Series from psi to MPa where appropriate.
    Values that are plausibly already in MPa (≤ 1000) are left unchanged.
    """
    if not pd.api.types.is_numeric_dtype(series):
        return series

    # Heuristic: treat values > 1000 as psi (since typical MPa values are < 1000)
    needs_conversion = series.abs() > 1000
    conversion_factor = 0.00689476
    series_converted = series.copy()
    series_converted[needs_conversion] = series[needs_conversion] * conversion_factor
    return series_converted

def _median_impute(df: pd.DataFrame, exclude: Optional[Set[str]] = None) -> pd.DataFrame:
    """
    Median‑impute missing numeric values. ``exclude`` can contain column names
    that should be left untouched (e.g., categorical identifiers).
    Returns the imputed DataFrame and writes a JSON file describing the
    original missingness.
    """
    if exclude is None:
        exclude = set()
    df = df.copy()
    missing_flags: Mapping[str, List[int]] = {}

    for col in df.columns:
        if col in exclude:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            missing_idx = df[col][df[col].isna()].index.tolist()
            if missing_idx:
                missing_flags[col] = missing_idx
                median_val = df[col].median(skipna=True)
                df[col].fillna(median_val, inplace=True)

    # Persist missingness information
    MISSING_FLAGS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with MISSING_FLAGS_JSON.open("w", encoding="utf-8") as f:
        json.dump(missing_flags, f, indent=2)
    log.debug("Missingness flags written to %s", MISSING_FLAGS_JSON)
    return df

def _apply_proxy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the deterministic residual‑stress proxy for every row:
        σ_res = k · heat_input · cooling_rate
    where ``k`` depends on ``material_class`` (see ``PROXY_COEFFICIENTS``).
    The proxy is stored in ``residual_stress_proxy``.  ``is_proxy`` is True
    when the original measured value is missing; otherwise it is False and
    the measured value is retained in the proxy column for completeness.
    Negative proxy values are clamped to ``PROXY_EPSILON``.
    """
    df = df.copy()

    # Ensure required columns exist
    required = {"material_class", "heat_input", "cooling_rate", "residual_stress_measured"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for proxy computation: {missing}")

    # Compute proxy
    def compute(row):
        k = PROXY_COEFFICIENTS.get(row["material_class"], 0.0)
        proxy_val = k * row["heat_input"] * row["cooling_rate"]
        # Clamp negative values
        if proxy_val < PROXY_EPSILON:
            proxy_val = PROXY_EPSILON
        return proxy_val

    df["residual_stress_proxy"] = df.apply(compute, axis=1)

    # Determine where we need to replace missing measured values
    is_missing = df["residual_stress_measured"].isna()
    df["is_proxy"] = is_missing

    # For rows where measured is present, overwrite proxy with the measured value
    df.loc[~is_missing, "residual_stress_proxy"] = df.loc[~is_missing, "residual_stress_measured"]

    # Ensure the proxy column has no missing values
    if df["residual_stress_proxy"].isna().any():
        raise RuntimeError("Proxy column contains NaNs after computation.")

    return df

def _validate_schema(df: pd.DataFrame, schema_path: Path) -> None:
    """
    Validate the DataFrame against the JSON‑Schema located at ``schema_path``.
    Raises ``jsonschema.exceptions.ValidationError`` on first failure.
    """
    log.debug("Loading schema from %s", schema_path)
    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    validator = Draft7Validator(schema)

    # Validate each row as a dict
    for idx, row in df.iterrows():
        # Convert pandas types to native Python types for jsonschema
        row_dict = row.to_dict()
        # Ensure ``other_process_params`` is a JSON‑encoded string (as required)
        if isinstance(row_dict.get("other_process_params"), (dict, list)):
            row_dict["other_process_params"] = json.dumps(row_dict["other_process_params"])
        try:
            validator.validate(row_dict)
        except Exception as exc:
            raise ValueError(f"Schema validation failed for row {idx}: {exc}") from exc

# ----------------------------------------------------------------------
# Core ingestion function
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
    output_path: Path
        Destination for the unified CSV.  Parent directories are created
        automatically.
    raw_csv_paths: list[Path] | None
        If provided, these files are used as the sole input sources.
        Otherwise the two bundled raw CSVs are loaded from
        ``data/raw``.
    limit_rows: int | None
        Optional cap on the number of rows to read (useful for quick tests).

    Returns
    -------
    pd.DataFrame
        The unified, processed DataFrame.
    """
    # ------------------------------------------------------------------
    # 1. Determine input files
    # ------------------------------------------------------------------
    if raw_csv_paths is None:
        raw_dir = paths.raw()
        # The repository defines exactly two bundled CSVs
        raw_csv_paths = [
            raw_dir / "pipeline_verification.csv",
            raw_dir / "synthetic_fatigue.csv",
        ]
    else:
        # Ensure we work with a list of Path objects
        raw_csv_paths = [Path(p) for p in raw_csv_paths]

    # Verify that each requested file exists
    for p in raw_csv_paths:
        if not p.is_file():
            raise FileNotFoundError(f"Raw data file not found: {p}")

    # ------------------------------------------------------------------
    # 2. Load data (CSV + optional JSON fixtures)
    # ------------------------------------------------------------------
    records: List[Mapping] = []
    for path in raw_csv_paths:
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path, dtype=object)  # keep everything as string initially
            if limit_rows:
                df = df.head(limit_rows)
            records.extend(df.to_dict(orient="records"))
        elif path.suffix.lower() == ".json":
            # Load a single JSON object (fixture) and treat it as one record
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # Flatten any nested dictionaries that correspond to ``other_process_params``
            if isinstance(data.get("other_process_params"), dict):
                data["other_process_params"] = json.dumps(data["other_process_params"])
            records.append(data)
        else:
            raise ValueError(f"Unsupported raw file type: {path}")

    if not records:
        raise RuntimeError("No records were loaded from the raw inputs.")

    df = pd.DataFrame(records)

    # ------------------------------------------------------------------
    # 3. Coerce numeric columns (heat_input, cooling_rate, elastic_modulus,
    #    yield_strength, residual_stress_measured, residual_stress_proxy)
    # ------------------------------------------------------------------
    numeric_cols = [
        "heat_input",
        "cooling_rate",
        "elastic_modulus",
        "yield_strength",
        "residual_stress_measured",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ------------------------------------------------------------------
    # 4. Unit standardisation (psi → MPa) for stress columns
    # ------------------------------------------------------------------
    stress_cols = ["residual_stress_measured"]
    for col in stress_cols:
        if col in df.columns:
            df[col] = _convert_psi_to_mpa(df[col])

    # ------------------------------------------------------------------
    # 5. Median imputation (excluding identifier / categorical columns)
    # ------------------------------------------------------------------
    exclude_cols = {"sample_id", "material_class", "source", "other_process_params", "checksum"}
    df = _median_impute(df, exclude=exclude_cols)

    # ------------------------------------------------------------------
    # 6. Compute residual‑stress proxy and flag proxy usage
    # ------------------------------------------------------------------
    df = _apply_proxy(df)

    # ------------------------------------------------------------------
    # 7. Add per‑row checksum
    # ------------------------------------------------------------------
    df = _add_checksum(df)

    # ------------------------------------------------------------------
    # 8. Validate against the JSON‑Schema
    # ------------------------------------------------------------------
    schema_path = Path(
        "specs/001-predicting-the-impact-of-residual-stress/contracts/dataset_schema.yaml"
    )
    _validate_schema(df, schema_path)

    # ------------------------------------------------------------------
    # 9. Write the unified CSV
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info("Unified dataset written to %s (%d rows)", output_path, len(df))

    return df

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the data ingestion pipeline.")
    parser.add_argument(
        "--output",
        type=Path,
        default=UNIFIED_CSV,
        help="Path to write the unified CSV (default: data/processed/unified_fatigue.csv).",
    )
    parser.add_argument(
        "--raw",
        nargs="+",
        type=Path,
        help="Optional list of raw CSV/JSON files to ingest (overrides the bundled defaults).",
    )
    parser.add_argument(
        "--limit-rows",
        type=int,
        default=None,
        help="Optional limit on the number of rows to read from each input (for testing).",
    )
    return parser

def main(argv: Optional[List[str]] = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    try:
        run_ingest(
            output_path=args.output,
            raw_csv_paths=args.raw,
            limit_rows=args.limit_rows,
        )
    except Exception as exc:
        log.error("Ingestion failed: %s", exc)
        sys.exit(1)

if __name__ == "__main__":
    main()