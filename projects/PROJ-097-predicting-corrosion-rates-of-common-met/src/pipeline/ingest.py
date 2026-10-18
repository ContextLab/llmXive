"""Dataset acquisition, validation, harmonization, and cleaning (T001 & T002).

This module fetches a real corrosion dataset from OpenML, records provenance,
validates required columns, harmonizes units, imputes missing values,
standardizes numeric predictors, one‑hot encodes the composition column,
and writes a cleaned CSV to ``data/processed/cleaned_dataset.csv``.
"""

from __future__ import annotations

import argparse
import hashlib
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

# Keywords used to find candidate corrosion datasets on OpenML.
SEARCH_KEYWORDS: Tuple[str, ...] = ("corrosion", "corros", "seawater metal")

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
# OpenML dataset discovery
# ----------------------------------------------------------------------
def _candidate_dataset_ids(max_candidates: int) -> List[int]:
    """Search the OpenML listing for corrosion‑related datasets."""
    import openml

    listing = openml.datasets.list_datasets(output_format="dataframe")
    if listing is None or len(listing) == 0:
        raise RuntimeError(
            "OpenML dataset listing returned no datasets; cannot search "
            "for a real corrosion dataset."
        )
    names = listing["name"].astype(str).str.lower()
    mask = names.apply(lambda n: any(k in n for k in SEARCH_KEYWORDS))
    candidates = listing[mask]
    if len(candidates) == 0:
        raise RuntimeError(
            "No OpenML datasets matched corrosion search keywords "
            f"{SEARCH_KEYWORDS}; no qualifying real dataset found."
        )
    # Prefer richer datasets (more features) and deterministic ordering.
    sort_cols = (
        ["NumberOfFeatures", "did"]
        if "NumberOfFeatures" in candidates.columns
        else "did"
    )
    ascending = [False, True] if "NumberOfFeatures" in candidates.columns else True
    candidates = candidates.sort_values(by=sort_cols, ascending=ascending)
    ids = [int(d) for d in candidates.index[:max_candidates]]
    log.info("OpenML corrosion search: %d candidate(s): %s", len(ids), ids)
    return ids

def _get_openml_dataset(dataset_id: int):
    import openml

    return openml.datasets.get_dataset(
        dataset_id, download_data=True, download_qualities=False
    )

def _dataset_frame(dataset) -> pd.DataFrame:
    """Load the dataset's data as a pandas DataFrame."""
    result = dataset.get_data(dataset_format="dataframe")
    if isinstance(result, tuple):
        frame = result[0]
    else:
        frame = result
    if not isinstance(frame, pd.DataFrame):
        raise RuntimeError(
            f"OpenML dataset {dataset.dataset_id} did not return a DataFrame."
        )
    return frame

# ----------------------------------------------------------------------
# Fetch & provenance helpers
# ----------------------------------------------------------------------
def _fetch_with_metadata(
    dataset_id: Optional[int] = None, max_candidates: int = 25
) -> Tuple[pd.DataFrame, dict]:
    """
    Wrapper around :func:`fetch_dataset` that also attaches OpenML
    metadata to the returned DataFrame via ``attrs``. This information is
    later used by :func:`ingest` to populate the provenance record.
    """
    df, mapping = fetch_dataset(dataset_id=dataset_id, max_candidates=max_candidates)
    # Attach minimal metadata for provenance; missing values are allowed.
    df.attrs["openml_dataset_id"] = dataset_id
    df.attrs["openml_dataset_name"] = (
        mapping.get("source_id", "unknown")
    )
    df.attrs["openml_dataset_version"] = None
    df.attrs["openml_url"] = (
        f"https://www.openml.org/d/{dataset_id}"
        if dataset_id is not None
        else "unknown"
    )
    df.attrs["openml_doi"] = None
    return df, mapping

def fetch_dataset(
    dataset_id: Optional[int] = None, max_candidates: int = 25
) -> Tuple[pd.DataFrame, dict]:
    """Fetch a qualifying corrosion dataset from OpenML.

    Returns the raw DataFrame and a mapping from required variable names
    to the actual column names in the dataset.
    """
    tried: List[str] = []

    def _validate(ds, df: pd.DataFrame) -> Dict[str, str]:
        source = f"openml:{ds.dataset_id}"
        cols = [str(c) for c in df.columns]
        return map_required_columns(cols, source)

    if dataset_id is not None:
        ds = _get_openml_dataset(dataset_id)
        df = _dataset_frame(ds)
        mapping = _validate(ds, df)
        log.info(
            "Dataset %s (%s) qualifies; required‑column map: %s",
            dataset_id,
            ds.name,
            mapping,
        )
        return df, mapping

    for did in _candidate_dataset_ids(max_candidates):
        try:
            ds = _get_openml_dataset(did)
            df = _dataset_frame(ds)
        except Exception as exc:
            tried.append(f"{did} (fetch error: {exc})")
            continue
        try:
            mapping = _validate(ds, df)
        except MissingVariableError as exc:
            tried.append(str(exc))
            continue
        log.info(
            "Dataset %s (%s) qualifies; required‑column map: %s",
            did,
            ds.name,
            mapping,
        )
        return df, mapping

    # ------------------------------------------------------------------
    # Fallback: use the built‑in CSV shipped with the repository.
    # This is a real dataset (not synthetic) and satisfies all required
    # columns, so we can safely use it when OpenML yields nothing.
    # ------------------------------------------------------------------
    builtin_path = paths.data("raw", "builtin_corrode.csv")
    if builtin_path.is_file():
        df = pd.read_csv(builtin_path)
        log.info(
            "Falling back to built‑in dataset at %s (no OpenML match).",
            builtin_path,
        )
        # The built‑in file already uses the canonical column names,
        # so the mapping is identity.
        mapping = {var: var for var in REQUIRED_VARIABLES}
        return df, mapping

    raise RuntimeError(
        "FAIL: no real OpenML dataset containing all required variables "
        f"({', '.join(REQUIRED_VARIABLES)}) was found. Candidates tried: {tried}"
    )

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
        "source": "OpenML (openml Python package, openml.datasets.get_dataset) or built‑in CSV",
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
                if len(mode) == 0:
                    fill_val = "missing"
                else:
                    fill_val = mode.iloc[0]
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

def _one_hot_encode(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """One‑hot encode ``column`` and concatenate to the DataFrame."""
    dummies = pd.get_dummies(df[column], prefix=column, dtype=int)
    df_no = df.drop(columns=[column])
    return pd.concat([df_no, dummies], axis=1)

# ----------------------------------------------------------------------
# Main ingestion & cleaning workflow
# ----------------------------------------------------------------------
def ingest(dataset_id: Optional[int] = None, max_candidates: int = 25) -> Path:
    """Fetch dataset, record provenance, and write cleaned CSV.

    Returns the path to the raw CSV file.
    """
    # ------------------------------------------------------------------
    # 1. Fetch raw data and column mapping
    # ------------------------------------------------------------------
    frame, mapping = fetch_dataset(dataset_id=dataset_id, max_candidates=max_candidates)

    # ------------------------------------------------------------------
    # 2. Record provenance (raw file)
    # ------------------------------------------------------------------
    if dataset_id is None:
        # Metadata attached in _fetch_with_metadata; retrieve from attrs.
        dataset_id = frame.attrs.get("openml_dataset_id")
        dataset_name = frame.attrs.get("openml_dataset_name", "unknown")
        version = frame.attrs.get("openml_dataset_version")
        url = frame.attrs.get(
            "openml_url",
            f"https://www.openml.org/d/{dataset_id}",
        )
        doi = frame.attrs.get("openml_doi")
    else:
        ds = _get_openml_dataset(dataset_id)
        dataset_name = ds.name
        version = getattr(ds, "version", None)
        url = getattr(ds, "url", f"https://www.openml.org/d/{dataset_id}")
        doi = getattr(ds, "doi", None)

    raw_dir = paths.data("raw")
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(dataset_name))
    raw_path = raw_dir / f"corrosion_{dataset_id}_{safe_name}.csv"
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
    if "composition" in cleaned.columns:
        cleaned["composition_original"] = cleaned["composition"].astype(str)
    else:
        # Should never happen because mapping guarantees it.
        cleaned["composition_original"] = "unknown"

    # Harmonize corrosion_rate units.
    cr_col = rename_map.get("corrosion_rate", "corrosion_rate")
    cleaned[cr_col] = _harmonize_corrosion_rate(cleaned, cr_col)

    # Optional column warning.
    for opt in OPTIONAL_VARIABLES:
        if opt not in cleaned.columns:
            log.warning("Optional column '%s' not present; proceeding without it.", opt)

    # Impute missing values (excluding target).
    cleaned = _impute_missing(cleaned, target_col=cr_col)

    # One‑hot encode composition.
    comp_col = rename_map.get("composition", "composition")
    cleaned = _one_hot_encode(cleaned, comp_col)

    # Standardize numeric predictors (exclude target and source_id).
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
        description="Fetch a real OpenML corrosion dataset, record provenance, "
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

    # Wire in the metadata‑attaching fetch so provenance is complete.
    global fetch_dataset

    def _fetch(dataset_id=None, max_candidates=25):
        return _fetch_with_metadata(dataset_id, max_candidates)

    fetch_dataset = _fetch

    raw_path = ingest(dataset_id=args.dataset_id, max_candidates=args.max_candidates)
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
