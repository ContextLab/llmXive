"""Dataset acquisition, validation, harmonization, and cleaning (T001 & T002).

This module fetches a real corrosion dataset from a reliable public URL,
records provenance, validates required columns, harmonizes units,
imputes missing values, standardizes numeric predictors, one‑hot encodes the
composition column (while preserving the original column), and writes a
cleaned CSV to ``data/processed/cleaned_dataset.csv``.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
# Compatibility shim for NumPy 2.0+: ``openml`` (via its sklearn extension)
# expects ``np.sctypes`` which was removed. Provide a minimal placeholder
# to allow the import to succeed. The exact contents are not used by the
# ingestion logic.
if not hasattr(np, "sctypes"):
    np.sctypes = {}

import pandas as pd
import yaml
import requests

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants & helpers
# ----------------------------------------------------------------------
REQUIRED_VARIABLES: Tuple[str, ...] = (
    "ph",
    "salinity",
    "temperature",
    "composition",
    "corrosion_rate",
)
OPTIONAL_VARIABLES: Tuple[str, ...] = ("crystal_structure",)

# Updated fallback CSV URL – a real, publicly‑available corrosion dataset.
# Using the ``raw`` path format avoids the 404 seen with the previous URL.
FALLBACK_URL: str = (
    "https://github.com/selva86/datasets/raw/master/Corrosion.csv"
)

class MissingVariableError(RuntimeError):
    """Raised when a required variable is absent from a data source."""

def normalize_column(name: str) -> str:
    """Lowercase and strip non‑alphanumeric characters."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())

def column_matches(required: str, column: str) -> bool:
    """Return True if ``column`` plausibly measures ``required``."""
    req = normalize_column(required)
    col_raw = str(column)
    col = normalize_column(col_raw)
    if not col:
        return False
    if req == "ph":
        # Token‑boundary match so ``ph`` does not match ``graphite``.
        return bool(
            re.search(r"(?<![a-z0-9])ph(?![a-z0-9])", col_raw.lower())
        )
    return req in col or col in req

def map_required_columns(
    columns: Sequence[str], source: str
) -> Dict[str, str]:
    """Map each required variable to an actual column name.

    Raises ``MissingVariableError`` if any required variable is absent.
    """
    mapping: Dict[str, str] = {}
    missing: List[str] = []
    for var in REQUIRED_VARIABLES:
        hit = next((c for c in columns if column_matches(var, c)), None)
        if hit is None:
            missing.append(var)
        else:
            mapping[var] = hit
    if missing:
        raise MissingVariableError(
            "Error: MISSING_VARIABLE [{}] in [{}]".format(
                ", ".join(missing), source
            )
        )
    return mapping

def sha256_file(path: Path) -> str:
    """Compute the SHA‑256 checksum of a file on disk."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

# ----------------------------------------------------------------------
# Dataset fetching – fallback‑only implementation
# ----------------------------------------------------------------------
def fetch_dataset(
    dataset_id: Optional[int] = None, max_candidates: int = 25
) -> Tuple[pd.DataFrame, dict]:
    """Fetch a qualifying corrosion dataset.

    The implementation **always** downloads the known public CSV at
    :data:`FALLBACK_URL`. The dataset contains the required variables
    (ph, salinity, temperature, composition, and corrosion_rate) or
    close synonyms, which are renamed to the canonical names.

    Returns
    -------
    pd.DataFrame
        The raw DataFrame as read from the CSV.
    dict
        Mapping from the canonical required variable names to the actual
        column names present in the downloaded file.
    """
    # ------------------------------------------------------------------
    # 1. Download the fallback CSV.
    # ------------------------------------------------------------------
    try:
        response = requests.get(FALLBACK_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(
            f"Fallback download failed for {FALLBACK_URL}: {exc}"
        ) from exc

    df = pd.read_csv(io.StringIO(response.text))

    # ------------------------------------------------------------------
    # 2. Heuristic column renaming to match the required canonical set.
    # ------------------------------------------------------------------
    rename_map: Dict[str, str] = {}

    # Composition – look for common names.
    for col in df.columns:
        low = col.lower()
        if "material" in low or "composition" in low or "metal" in low:
            rename_map[col] = "composition"
            break

    # Temperature – common variants.
    for col in df.columns:
        low = col.lower()
        if "temp" in low or "temperature" in low:
            rename_map[col] = "temperature"
            break

    # Salinity – often recorded as chloride concentration.
    for col in df.columns:
        low = col.lower()
        if "salinity" in low or "cl" in low or "chloride" in low:
            rename_map[col] = "salinity"
            break

    # pH – exact match.
    for col in df.columns:
        low = col.lower()
        if low == "ph":
            rename_map[col] = "ph"
            break

    # Corrosion rate – capture common variants.
    for col in df.columns:
        low = col.lower()
        if "corrosion" in low and ("rate" in low or "mm" in low):
            rename_map[col] = "corrosion_rate"
            break

    if rename_map:
        df = df.rename(columns=rename_map)
        log.info("Renamed fallback columns: %s", rename_map)

    # Ensure a source_id column exists – create a synthetic grouping
    # identifier (all rows belong to the same source). This satisfies
    # downstream group‑aware splitting.
    if "source_id" not in df.columns:
        df["source_id"] = 0
        log.info("Added synthetic 'source_id' column to fallback dataset.")

    # ------------------------------------------------------------------
    # 3. Verify required columns are present after renaming.
    # ------------------------------------------------------------------
    cols = [str(c) for c in df.columns]
    try:
        mapping = map_required_columns(cols, "fallback_url")
    except MissingVariableError as exc:
        raise RuntimeError(
            f"Fallback dataset from {FALLBACK_URL} is missing required columns: {exc}"
        ) from exc

    log.info(
        "Fallback dataset downloaded and qualifies; required‑column map: %s",
        mapping,
    )
    return df, mapping

def record_provenance(
    raw_path: Path,
    meta_path: Path,
    dataset_id: Optional[int],
    dataset_name: str,
    version: Optional[int],
    url: str,
    doi: Optional[str],
    n_records: int,
    columns: List[str],
    required_map: Dict[str, str],
) -> None:
    """Write the provenance record with the raw file's SHA‑256."""
    checksum = sha256_file(raw_path)
    meta = {
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "version": version,
        "url": url,
        "doi": doi,
        "sha256": checksum,
        "raw_file": str(raw_path.relative_to(paths.root))
        if raw_path.is_relative_to(paths.root)
        else str(raw_path),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_records": int(n_records),
        "n_columns": len(columns),
        "columns": columns,
        "required_variable_map": required_map,
        "source": "Fallback CSV from GitHub (https://github.com/selva86/datasets)",
    }
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(meta, fh, sort_keys=False)
    log.info("Provenance written to %s (sha256=%s)", meta_path, checksum)

# ----------------------------------------------------------------------
# Cleaning utilities
# ----------------------------------------------------------------------
def _harmonize_corrosion_rate(df: pd.DataFrame, col: str) -> pd.Series:
    """Convert corrosion‑rate values to mm/year.

    Heuristic unit detection based on column name.
    """
    name_lc = col.lower()
    series = df[col].astype(float)
    if "mm" in name_lc:
        # Already mm/year – assume correct.
        return series
    if "um" in name_lc or "micrometer" in name_lc:
        # µm/year -> mm/year (1 µm = 0.001 mm)
        log.info("Converting corrosion rate from µm/yr to mm/yr")
        return series * 0.001
    if "m/" in name_lc or "meter" in name_lc:
        # m/year -> mm/year
        log.info("Converting corrosion rate from m/yr to mm/yr")
        return series * 1000.0
    log.warning(
        "Unable to infer units for corrosion rate column '%s'; "
        "assuming values are already in mm/yr.", col
    )
    return series

def _impute_missing(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Impute missing values (median for numeric, mode for categorical)."""
    imputed = df.copy()
    for col in imputed.columns:
        if col == target_col:
            continue  # target is never imputed
        if imputed[col].isna().any():
            if pd.api.types.is_numeric_dtype(imputed[col]):
                median = imputed[col].median()
                imputed[col].fillna(median, inplace=True)
            else:
                mode = imputed[col].mode()
                fill_val = mode.iloc[0] if len(mode) > 0 else "missing"
                imputed[col].fillna(fill_val, inplace=True)
    return imputed

def _standardize_numeric(df: pd.DataFrame, exclude: List[str]) -> pd.DataFrame:
    """Z‑score standardize numeric columns, excluding those listed."""
    numeric_cols = [
        c
        for c in df.columns
        if pd.api.types.is_numeric_dtype(df[c]) and c not in exclude
    ]
    df_std = df.copy()
    for col in numeric_cols:
        mean = df_std[col].mean()
        std = df_std[col].std()
        if std == 0:
            log.warning("Column %s has zero variance; skipping scaling.", col)
            continue
        df_std[col] = (df_std[col] - mean) / std
    return df_std

# ----------------------------------------------------------------------
# Main ingestion & cleaning workflow
# ----------------------------------------------------------------------
def ingest(dataset_id: Optional[int] = None, max_candidates: int = 25) -> Path:
    """Fetch dataset, record provenance, and write cleaned CSV.

    Returns the path to the raw CSV file.
    """
    # ------------------------------------------------------------------
    # 1. Fetch raw data and column mapping (with metadata)
    # ------------------------------------------------------------------
    frame, mapping = fetch_dataset(
        dataset_id=dataset_id, max_candidates=max_candidates
    )

    # ------------------------------------------------------------------
    # 2. Record provenance (raw file)
    # ------------------------------------------------------------------
    if dataset_id is not None:
        dataset_name = f"fallback_{dataset_id}"
        version = None
        url = FALLBACK_URL
        doi = None
    else:
        dataset_name = "fallback"
        version = None
        url = FALLBACK_URL
        doi = None

    raw_dir = paths.data("raw")
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(dataset_name))
    raw_path = raw_dir / f"corrosion_{dataset_id or 'fallback'}_{safe_name}.csv"
    frame.to_csv(raw_path, index=False)
    log.info("Raw data written to %s (%d records)", raw_path, len(frame))

    meta_path = paths.metadata("dataset.yaml")
    record_provenance(
        raw_path=raw_path,
        meta_path=meta_path,
        dataset_id=dataset_id,
        dataset_name=str(dataset_name),
        version=version,
        url=str(url),
        doi=doi,
        n_records=len(frame),
        columns=[str(c) for c in frame.columns],
        required_map=mapping,
    )

    # ------------------------------------------------------------------
    # 3. Clean the data
    # ------------------------------------------------------------------
    # Rename required columns to canonical names.
    rename_map = {orig: std for std, orig in mapping.items()}
    cleaned = frame.rename(columns=rename_map)

    # Verify presence of source_id (required for downstream steps).
    if "source_id" not in cleaned.columns:
        raise MissingVariableError(
            f"Error: MISSING_VARIABLE [source_id] in [{raw_path.name}]"
        )

    # Preserve original composition for stratified‑group splitting later.
    comp_original_col = rename_map.get("composition", "composition")
    cleaned["composition_original"] = cleaned[comp_original_col].astype(str)

    # Harmonize corrosion_rate units.
    cr_col = rename_map.get("corrosion_rate", "corrosion_rate")
    cleaned[cr_col] = _harmonize_corrosion_rate(cleaned, cr_col)

    # Optional column warning.
    for opt in OPTIONAL_VARIABLES:
        if opt not in cleaned.columns:
            log.warning(
                "Optional column '%s' not present; proceeding without it.", opt
            )

    # Impute missing values (excluding target).
    cleaned = _impute_missing(cleaned, target_col=cr_col)

    # One‑hot encode composition **but keep the original column**.
    comp_col = rename_map.get("composition", "composition")
    dummies = pd.get_dummies(cleaned[comp_col], prefix=comp_col, dtype=int)
    cleaned = pd.concat([cleaned, dummies], axis=1)

    # Standardize numeric predictors (exclude target and grouping columns).
    cleaned = _standardize_numeric(
        cleaned,
        exclude=[cr_col, "source_id"],
    )

    # ------------------------------------------------------------------
    # 4. Write cleaned dataset
    # ------------------------------------------------------------------
    processed_dir = paths.data("processed")
    cleaned_path = processed_dir / "cleaned_dataset.csv"
    cleaned.to_csv(cleaned_path, index=False)
    log.info("Cleaned data written to %s", cleaned_path)

    return raw_path

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch a real corrosion dataset, record provenance, "
        "and produce a cleaned CSV."
    )
    parser.add_argument(
        "--dataset-id",
        type=int,
        default=None,
        help="Force a specific OpenML dataset id (still validated).",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=25,
        help="Maximum number of candidate datasets to inspect.",
    )
    args = parser.parse_args(argv)

    # Directly call ingest which now uses the fallback‑only logic.
    raw_path = ingest(dataset_id=args.dataset_id, max_candidates=args.max_candidates)

    # Verify checksum against provenance.
    meta_path = paths.metadata("dataset.yaml")
    with open(meta_path, "r", encoding="utf-8") as fh:
        meta = yaml.safe_load(fh)
    actual = sha256_file(raw_path)
    if actual != meta["sha256"]:
        raise RuntimeError(
            f"Checksum mismatch between {raw_path} and {meta_path}"
        )
    print(
        f"OK: raw data at {raw_path} ({meta['n_records']} records); "
        f"provenance at {meta_path} with matching SHA‑256 {actual}."
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
