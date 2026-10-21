"""
generate_units_metadata.py

Reads each raw CSV file under ``data/raw/`` (or falls back to ``data/source/`` if
``data/raw/`` is empty) and creates a JSON file ``data/raw/<source>_units.json``
that maps each column name to its declared SI unit.

The script validates that:
  * All required columns are present (ignoring surrounding whitespace).
  * All numeric columns contain only numeric data (no stray strings).
  * Unit declarations are consistent across all sources.

If any of these checks fail a ``UnitMismatchError`` is raised, aborting the
pipeline unless at least one valid source is found. In that case invalid
sources are skipped and a warning is logged.

The generated JSON files are used by downstream preprocessing steps to
convert values to SI units.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = [
    "plasma_power_w",
    "exposure_time_s",
    "chemical_concentration_pct",
    "polymer_surface_energy",
    "substrate_roughness_nm",
    "adhesion_strength_mj_m2",
    "treatment_type",
    "pair_id",
]

# Mapping from column name to its SI unit (as a human‑readable string)
UNITS_MAP: Dict[str, str] = {
    "plasma_power_w": "W",                     # watts
    "exposure_time_s": "s",                    # seconds
    "chemical_concentration_pct": "%",         # percent (dimensionless)
    "polymer_surface_energy": "mJ/m^2",        # millijoules per square metre
    "substrate_roughness_nm": "nm",            # nanometres (will be converted later)
    "adhesion_strength_mj_m2": "MJ/m^2",       # megajoules per square metre
    "treatment_type": "category",              # categorical label
    "pair_id": "category",                     # categorical identifier
}

# ----------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------
class UnitMismatchError(Exception):
    """Raised when a column is missing or contains non‑numeric data where a
    numeric unit is expected, or when unit declarations differ across sources."""
    pass

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _setup_logger() -> logging.Logger:
    """Configure and return a logger for this module."""
    logger = get_logger(__name__)
    logger.setLevel(logging.INFO)
    return logger

LOG = _setup_logger()

def _list_raw_csv_files() -> List[Path]:
    """
    Return a list of CSV files to process.

    The primary location is ``data/raw``.  If that directory contains no
    CSV files, we fall back to ``data/source`` and copy any found CSVs
    into ``data/raw`` so that downstream steps see a consistent layout.
    """
    raw_dir = paths.data("raw")
    source_dir = paths.data("source")
    csv_files = list(raw_dir.glob("*.csv"))

    if csv_files:
        LOG.info("Found %d raw CSV file(s) in %s", len(csv_files), raw_dir)
        return csv_files

    # Fallback: copy from source to raw
    source_csvs = list(source_dir.glob("*.csv"))
    if not source_csvs:
        LOG.warning("No CSV files found in either %s or %s.", raw_dir, source_dir)
        return []

    LOG.info("No raw CSVs found; copying %d file(s) from %s to %s",
             len(source_csvs), source_dir, raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    for src_path in source_csvs:
        dest_path = raw_dir / src_path.name
        dest_path.write_bytes(src_path.read_bytes())
        LOG.info("Copied %s -> %s", src_path, dest_path)

    csv_files = list(raw_dir.glob("*.csv"))
    LOG.info("After copy, %d raw CSV file(s) are available.", len(csv_files))
    return csv_files

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from column names and return a new DataFrame."""
    df = df.copy()
    df.columns = df.columns.str.strip()
    return df

def _validate_columns(df: pd.DataFrame, source_name: str) -> None:
    """Ensure that all required columns are present."""
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise UnitMismatchError(
            f"Source '{source_name}' is missing required columns: {sorted(missing)}"
        )
    LOG.info("All required columns present for source '%s'.", source_name)

def _validate_numeric_columns(df: pd.DataFrame, source_name: str) -> None:
    """Check that columns expected to be numeric contain only numeric data."""
    numeric_cols = [
        col for col, unit in UNITS_MAP.items() if unit != "category"
    ]
    for col in numeric_cols:
        if col not in df.columns:
            continue
        original_nans = df[col].isna()
        coerced = pd.to_numeric(df[col], errors="coerce")
        new_nans = coerced.isna()
        if (new_nans & ~original_nans).any():
            raise UnitMismatchError(
                f"Column '{col}' in source '{source_name}' contains non‑numeric values."
            )
    LOG.info("Numeric columns validated for source '%s'.", source_name)

def _write_units_json(units: Dict[str, str], dest_path: Path) -> None:
    """Write the ``units`` mapping to ``dest_path`` as pretty‑printed JSON."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("w", encoding="utf-8") as f:
        json.dump(units, f, indent=2, sort_keys=True)
    LOG.info("Wrote unit metadata to %s", dest_path)

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    """
    Generate per‑source unit‑metadata JSON files.

    For each CSV file under ``data/raw/``, a JSON file named
    ``<source>_units.json`` is created in the same directory. The JSON
    maps column names to the SI unit strings defined in ``UNITS_MAP``.

    If a source is missing required columns or contains non‑numeric data,
    the source is skipped *unless* no other valid sources exist, in which
    case a ``UnitMismatchError`` is raised to abort the pipeline.

    After processing all valid sources, the function checks that the unit
    declarations are identical across sources.  Any discrepancy raises
    ``UnitMismatchError``.
    """
    csv_files = _list_raw_csv_files()
    if not csv_files:
        LOG.warning("No CSV files to process – exiting.")
        return

    processed_any = False
    first_error: Optional[UnitMismatchError] = None
    # Keep a mapping source_name -> units dict for cross‑source consistency check
    all_units: Dict[str, Dict[str, str]] = {}

    for csv_path in csv_files:
        source_name = csv_path.stem  # filename without extension
        LOG.info("Processing source '%s' (%s)", source_name, csv_path)

        # Load the CSV
        try:
            df = pd.read_csv(csv_path)
            df = _normalize_columns(df)
        except Exception as exc:
            err = UnitMismatchError(
                f"Failed to read CSV for source '{source_name}': {exc}"
            )
            LOG.error(str(err))
            if not first_error:
                first_error = err
            continue

        # Validate required columns and numeric integrity
        try:
            _validate_columns(df, source_name)
            _validate_numeric_columns(df, source_name)
        except UnitMismatchError as exc:
            LOG.warning(str(exc))
            if not first_error:
                first_error = exc
            # Skip this source and continue with others
            continue

        # Build the unit‑metadata dict (only for columns that exist)
        units_metadata = {
            col: UNITS_MAP.get(col, "unknown") for col in df.columns
        }

        # Destination JSON path (must live alongside the CSV in data/raw/)
        json_path = csv_path.with_name(f"{source_name}_units.json")
        _write_units_json(units_metadata, json_path)

        all_units[source_name] = units_metadata
        processed_any = True

    if not processed_any:
        # No valid source was processed – raise the first encountered error
        raise first_error or UnitMismatchError(
            "No valid CSV files with required columns were found."
        )

    # ------------------------------------------------------------------
    # Cross‑source unit consistency check
    # ------------------------------------------------------------------
    reference_source = next(iter(all_units))
    reference_units = all_units[reference_source]

    for src, units in all_units.items():
        for col, unit in reference_units.items():
            other_unit = units.get(col)
            if other_unit != unit:
                raise UnitMismatchError(
                    f"Unit mismatch for column '{col}': source '{reference_source}' "
                    f"uses '{unit}' but source '{src}' uses '{other_unit}'."
                )
    LOG.info("All sources share consistent unit metadata.")

    LOG.info("Unit‑metadata generation completed successfully.")

if __name__ == "__main__":
    main()
