"""
ingest.py
----------
Implements the ingestion pipeline for T002.

The script:
  1. Loads all raw CSV files (verification, synthetic, any external datasets).
  2. Verifies each file’s SHA‑256 checksum against ``data/raw/checksums.json``.
     Missing entries are added automatically.
  3. Converts residual‑stress units from psi → MPa using ``config.PSI_TO_MPA``.
  4. Median‑imputes missing numeric columns and records the original missingness
     in ``data/processed/missing_flags.json``.
  5. Computes the linear residual‑stress proxy
        σ_res = k · heat_input · cooling_rate
     where ``k`` comes from ``config.PROXY_COEFFICIENTS`` (steel = 0.8,
     aluminum = 0.6).  The proxy is stored in ``residual_stress_proxy`` and
     ``is_proxy`` is set to ``True`` when ``residual_stress_measured`` is missing.
  6. Clamps negative proxy values to ``config.PROXY_EPSILON`` (0.01 MPa) and
     logs the number of clamped rows to ``logs/proxy_clamp.log``.
  7. Adds a per‑row SHA‑256 checksum column ``checksum``.
  8. Validates the final DataFrame against the JSON‑Schema at
     ``specs/001-predicting-the-impact-of-residual-stress/contracts/dataset_schema.yaml``.
  9. Writes the unified dataset to ``data/processed/unified_fatigue.csv`` and the
     missing‑flags JSON to ``data/processed/missing_flags.json``.
"""
import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import List, Mapping, Optional, Set

import pandas as pd
import yaml
from jsonschema import Draft7Validator, ValidationError

from llmxive_toolkit import paths, get_logger
from src.config import (
    PROXY_COEFFICIENTS,
    PROXY_EPSILON,
    PSI_TO_MPA,
)

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
UNIFIED_CSV = paths.processed("unified_fatigue.csv")
MISSING_FLAGS_JSON = paths.processed("missing_flags.json")
PROXY_CLAMP_LOG = paths.logs("proxy_clamp.log")
CHECKSUMS_JSON = paths.raw("checksums.json")
SCHEMA_PATH = Path(
    "specs/001-predicting-the-impact-of-residual-stress/contracts/dataset_schema.yaml"
)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _file_checksum(path: Path) -> str:
    """Return the SHA‑256 checksum of the file *path*."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _row_checksum(row: pd.Series) -> str:
    """
    Compute a deterministic SHA‑256 checksum for a single DataFrame row.
    The row is converted to a JSON string with sorted keys to guarantee
    reproducibility.
    """
    row_dict = {
        k: (None if pd.isna(v) else v)
        for k, v in row.items()
    }
    json_bytes = json.dumps(row_dict, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(json_bytes).hexdigest()

def _load_checksums() -> Mapping[str, str]:
    """Load the JSON mapping of expected checksums (may be empty)."""
    if CHECKSUMS_JSON.is_file():
        with CHECKSUMS_JSON.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_checksums(mapping: Mapping[str, str]) -> None:
    """Persist the checksum mapping."""
    CHECKSUMS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with CHECKSUMS_JSON.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, sort_keys=True)

def _list_raw_csvs() -> List[Path]:
    """
    Return a list of raw CSV files that should be ingested:
    * ``pipeline_verification.csv``
    * ``synthetic_fatigue.csv``
    * any ``external_*.csv`` produced by T014.
    """
    raw_dir = paths.raw()
    candidates = [
        raw_dir / "pipeline_verification.csv",
        raw_dir / "synthetic_fatigue.csv",
    ]
    # Add external files (any CSV whose name starts with ``external_``)
    candidates.extend(sorted(raw_dir.glob("external_*.csv")))
    return [p for p in candidates if p.is_file()]

# ----------------------------------------------------------------------
# Core pipeline steps
# ----------------------------------------------------------------------
def _verify_checksums(csv_paths: List[Path]) -> Mapping[str, str]:
    """
    Verify each CSV file against the stored checksum.  Missing entries are
    added; mismatches raise a ``ValueError``.
    """
    checksums = dict(_load_checksums())
    for p in csv_paths:
        actual = _file_checksum(p)
        stored = checksums.get(str(p))
        if stored is None:
            log.info("No stored checksum for %s – adding it.", p)
            checksums[str(p)] = actual
        elif stored != actual:
            raise ValueError(
                f"Checksum mismatch for {p}: stored {stored}, actual {actual}"
            )
    # Persist any newly‑added entries
    _save_checksums(checksums)
    return checksums

def _load_and_concat(csv_paths: List[Path]) -> pd.DataFrame:
    """Read all CSVs and concatenate them row‑wise."""
    dfs = [pd.read_csv(p, dtype=str) for p in csv_paths]
    df = pd.concat(dfs, ignore_index=True)
    return df

def _convert_psi_to_mpa(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert residual‑stress values from psi to MPa where the ``stress_unit``
    column indicates ``psi``.  The conversion factor is ``config.PSI_TO_MPA``.
    """
    mask = df["stress_unit"] == "psi"
    # Convert measured stress if present
    if "residual_stress_measured" in df.columns:
        measured = pd.to_numeric(df.loc[mask, "residual_stress_measured"], errors="coerce")
        df.loc[mask, "residual_stress_measured"] = measured * PSI_TO_MPA
    # Convert any proxy column that may already exist (unlikely at this stage)
    if "residual_stress_proxy" in df.columns:
        proxy = pd.to_numeric(df.loc[mask, "residual_stress_proxy"], errors="coerce")
        df.loc[mask, "residual_stress_proxy"] = proxy * PSI_TO_MPA
    # Update the unit label to MPa for consistency
    df.loc[mask, "stress_unit"] = "MPa"
    return df

def _median_impute(df: pd.DataFrame, exclude: Optional[Set[str]] = None) -> pd.DataFrame:
    """
    Median‑impute missing numeric values. ``exclude`` can contain column names
    that should be left untouched (e.g., identifiers).
    Returns the imputed DataFrame and writes a JSON file describing the
    original missingness.
    """
    if exclude is None:
        exclude = set()
    missing_flags = {}
    numeric_cols = [
        c for c in df.select_dtypes(include=["number", "float", "int"]).columns
        if c not in exclude
    ]
    for col in numeric_cols:
        missing_idx = df[col].index[df[col].isna()].tolist()
        if missing_idx:
            missing_flags[col] = missing_idx
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
    # Write missing‑flags JSON
    MISSING_FLAGS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with MISSING_FLAGS_JSON.open("w", encoding="utf-8") as f:
        json.dump(missing_flags, f, indent=2, sort_keys=True)
    return df

def _apply_proxy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the linear residual‑stress proxy for every row:
        σ_res = k · heat_input · cooling_rate
    ``k`` depends on ``material_class`` (see ``PROXY_COEFFICIENTS``).
    Populate ``residual_stress_proxy`` and ``is_proxy``.
    Clamp negative proxy values to ``PROXY_EPSILON`` and log the count.
    """
    # Ensure numeric types
    df["heat_input"] = pd.to_numeric(df["heat_input"], errors="coerce")
    df["cooling_rate"] = pd.to_numeric(df["cooling_rate"], errors="coerce")

    proxy_vals = []
    for idx, row in df.iterrows():
        k = PROXY_COEFFICIENTS.get(row["material_class"], 0.0)
        val = k * row["heat_input"] * row["cooling_rate"]
        proxy_vals.append(val)

    df["residual_stress_proxy"] = proxy_vals

    # Determine which rows lack a measured stress
    measured_present = pd.to_numeric(df["residual_stress_measured"], errors="coerce").notna()
    df["is_proxy"] = ~measured_present

    # Clamp negatives
    negative_mask = df["residual_stress_proxy"] < 0
    clamp_count = negative_mask.sum()
    if clamp_count > 0:
        df.loc[negative_mask, "residual_stress_proxy"] = PROXY_EPSILON
    # Log clamp count
    PROXY_CLAMP_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PROXY_CLAMP_LOG.open("w", encoding="utf-8") as f:
        f.write(f"clamped_negative_proxy_rows: {int(clamp_count)}\n")
    return df

def _add_checksum(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``checksum`` column containing the per‑row SHA‑256 hash."""
    df["checksum"] = df.apply(_row_checksum, axis=1)
    return df

def _validate_schema(df: pd.DataFrame, schema_path: Path) -> None:
    """Validate ``df`` against the JSON‑Schema at ``schema_path``."""
    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    validator = Draft7Validator(schema)

    for idx, row in df.iterrows():
        # Convert pandas types → plain Python types for validation
        row_dict = row.to_dict()
        # ``other_process_params`` must be a JSON‑encoded string
        if isinstance(row_dict.get("other_process_params"), (dict, list)):
            row_dict["other_process_params"] = json.dumps(
                row_dict["other_process_params"]
            )
        try:
            validator.validate(row_dict)
        except ValidationError as exc:
            raise ValueError(
                f"Schema validation failed for row {idx}: {exc.message}"
            ) from exc

# ----------------------------------------------------------------------
# Public API
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
        Otherwise the default raw files are discovered automatically.
    limit_rows: int | None
        Optional cap on the number of rows to read (useful for quick tests).

    Returns
    -------
    pd.DataFrame
        The unified, processed DataFrame.
    """
    # ------------------------------------------------------------------
    # 1. Determine raw files
    # ------------------------------------------------------------------
    if raw_csv_paths is None:
        raw_paths = _list_raw_csvs()
    else:
        raw_paths = raw_csv_paths

    if not raw_paths:
        raise FileNotFoundError("No raw CSV files found for ingestion.")

    # ------------------------------------------------------------------
    # 2. Verify checksums (and augment the checksum store if needed)
    # ------------------------------------------------------------------
    _verify_checksums(raw_paths)

    # ------------------------------------------------------------------
    # 3. Load & concatenate
    # ------------------------------------------------------------------
    df = _load_and_concat(raw_paths)

    # Optional row limit (useful for testing)
    if limit_rows is not None:
        df = df.head(limit_rows)

    # ------------------------------------------------------------------
    # 4. Unit conversion
    # ------------------------------------------------------------------
    df = _convert_psi_to_mpa(df)

    # ------------------------------------------------------------------
    # 5. Median imputation (record missingness)
    # ------------------------------------------------------------------
    df = _median_impute(df, exclude={"sample_id", "material_class", "stress_unit", "source"})

    # ------------------------------------------------------------------
    # 6. Compute proxy and clamp negatives
    # ------------------------------------------------------------------
    df = _apply_proxy(df)

    # ------------------------------------------------------------------
    # 7. Add per‑row checksum
    # ------------------------------------------------------------------
    df = _add_checksum(df)

    # ------------------------------------------------------------------
    # 8. Schema validation
    # ------------------------------------------------------------------
    _validate_schema(df, SCHEMA_PATH)

    # ------------------------------------------------------------------
    # 9. Persist unified dataset
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info("Unified dataset written to %s (rows=%d)", output_path, len(df))

    return df

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest raw fatigue datasets.")
    parser.add_argument(
        "--output",
        type=Path,
        default=UNIFIED_CSV,
        help="Destination path for the unified CSV (default: data/processed/unified_fatigue.csv).",
    )
    parser.add_argument(
        "--raw",
        nargs="+",
        type=Path,
        help="Explicit list of raw CSV files to ingest (overrides automatic discovery).",
    )
    parser.add_argument(
        "--limit-rows",
        type=int,
        default=None,
        help="Optional limit on the number of rows to read (for quick tests).",
    )
    return parser

def main(argv: Optional[List[str]] = None) -> None:
    """CLI entry point."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    raw_paths = args.raw if args.raw else None
    try:
        run_ingest(
            output_path=args.output,
            raw_csv_paths=raw_paths,
            limit_rows=args.limit_rows,
        )
    except Exception as exc:
        log.error("Ingestion failed: %s", exc)
        sys.exit(1)

if __name__ == "__main__":
    main()
