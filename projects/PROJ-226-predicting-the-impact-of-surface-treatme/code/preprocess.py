"""
preprocess.py
----------------
Implements Task T004: parses raw CSV files, converts numeric fields to SI units,
canonicalises treatment types, one‑hot encodes categorical columns (including
``pair_id``), median‑impute missing numeric values per substrate class,
records imputation details, computes field‑coverage statistics, flags low‑coverage
columns, and writes the cleaned dataset.

Expected side‑effects:
  * data/cleaned/cleaned.csv                – the final cleaned table
  * data/cleaned/imputation_log.json        – details of median imputation
  * data/cleaned/field_coverage.json        – per‑column coverage percentages
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Mapping of non‑SI units to SI conversion factors.
# key: original unit string, value: (target SI unit, multiplication factor)
UNIT_CONVERSIONS = {
    "kW": ("W", 1_000.0),
    "KW": ("W", 1_000.0),
    "MW": ("W", 1_000_000.0),
    "min": ("s", 60.0),
    "minute": ("s", 60.0),
    # percent is already SI; keep for completeness
    "%": ("%", 1.0),
    "percent": ("%", 1.0),
}

# Canonical treatment type taxonomy.
TREATMENT_CANONICAL_MAP = {
    "O2 Plasma": "Oxygen Plasma",
    "O2-plasma": "Oxygen Plasma",
    "Oxygen Plasma": "Oxygen Plasma",
    "Nitrogen Plasma": "Nitrogen Plasma",
    "N2 Plasma": "Nitrogen Plasma",
    # extend as needed
}

# Columns that are required for the final schema (numeric fields + target).
REQUIRED_NUMERIC_COLUMNS = [
    "plasma_power_w",
    "exposure_time_s",
    "chemical_concentration_pct",
    "polymer_surface_energy",
    "substrate_roughness_nm",
    "adhesion_strength_mj_m2",
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_raw_csv_files() -> List[Path]:
    """Return a list of all CSV files in ``data/raw``."""
    raw_dir = paths.data("raw")
    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        raise RuntimeError(f"No raw CSV files found in {raw_dir}")
    return csv_files

def _load_units_metadata(csv_path: Path) -> Dict[str, str]:
    """
    Load the per‑source units JSON that lives alongside the CSV file.
    The JSON maps column names to unit strings.
    """
    json_path = csv_path.with_name(csv_path.stem + "_units.json")
    if not json_path.is_file():
        raise RuntimeError(f"Units metadata missing for {csv_path.name}")
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _apply_unit_conversions(df: pd.DataFrame, units: Dict[str, str]) -> pd.DataFrame:
    """
    Convert columns to SI using ``UNIT_CONVERSIONS`` where applicable.
    Columns whose unit is already SI are left untouched.
    """
    df_converted = df.copy()
    for col, unit in units.items():
        if col not in df_converted.columns:
            continue  # ignore stray entries
        target_unit, factor = UNIT_CONVERSIONS.get(unit, (unit, 1.0))
        if factor != 1.0:
            # Ensure numeric dtype before multiplication
            df_converted[col] = pd.to_numeric(df_converted[col], errors="coerce") * factor
        # No need to store the new unit; downstream steps use numeric values only.
    return df_converted

def _canonicalise_treatment_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map all known variants of ``treatment_type`` to a single canonical label.
    Unknown values are left unchanged (they will become separate one‑hot columns).
    """
    if "treatment_type" not in df.columns:
        raise RuntimeError("Column ``treatment_type`` missing from dataframe")
    df["treatment_type"] = df["treatment_type"].map(
        lambda x: TREATMENT_CANONICAL_MAP.get(x, x)
    )
    return df

def _one_hot_encode(df: pd.DataFrame, categorical_cols: List[str]) -> pd.DataFrame:
    """
    One‑hot encode the supplied categorical columns using pandas.get_dummies.
    Original columns are dropped.
    Missing categorical values are filled with the placeholder string ``__MISSING__``.
    """
    df_filled = df.copy()
    for col in categorical_cols:
        if col not in df_filled.columns:
            raise RuntimeError(f"Expected categorical column '{col}' not found.")
        # Fill NaNs so get_dummies creates a column for missing values
        df_filled[col] = df_filled[col].fillna("__MISSING__")
    df_encoded = pd.get_dummies(df_filled, columns=categorical_cols, drop_first=False, dtype=int)
    return df_encoded

def _compute_field_coverage(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Compute the percentage of non‑missing values per column.
    Returns a dict mapping column name → {"coverage_percent": float, "low_coverage": bool}
    where ``low_coverage`` is True when coverage < 80 %.
    """
    total = len(df)
    coverage_info: Dict[str, Dict] = {}
    for col in df.columns:
        non_missing = int(df[col].notna().sum())
        pct = (non_missing / total) * 100.0
        coverage_info[col] = {
            "coverage_percent": round(pct, 2),
            "low_coverage": pct < 80.0,
        }
    return coverage_info

def _median_impute_per_class(
    df: pd.DataFrame, class_col: str, numeric_cols: List[str]
) -> Tuple[pd.DataFrame, Dict]:
    """
    Median‑impute missing numeric values within each class (identified by ``class_col``).
    Returns the imputed dataframe and a log dict:
    {
        "<column_name>": {
            "<class_value>": <median_used>,
            ...
        },
        ...
    }
    """
    impute_log: Dict[str, Dict] = {}
    df_imputed = df.copy()

    for col in numeric_cols:
        if col not in df_imputed.columns:
            continue
        impute_log[col] = {}
        # Compute per‑class medians (skip NaNs)
        medians = (
            df_imputed.groupby(class_col)[col]
            .median()
            .rename("median")
            .reset_index()
        )
        class_to_median = dict(zip(medians[class_col], medians["median"]))

        def _fill(row):
            if pd.notna(row[col]):
                return row[col]
            cls = row[class_col]
            median = class_to_median.get(cls, np.nan)
            # Record the median used for this class (None if median is NaN)
            impute_log[col][str(cls)] = (
                float(median) if pd.notna(median) else None
            )
            return median

        df_imputed[col] = df_imputed.apply(_fill, axis=1)

    return df_imputed, impute_log

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the full preprocessing pipeline.

    Expected side‑effects:
      * data/cleaned/cleaned.csv
      * data/cleaned/imputation_log.json
      * data/cleaned/field_coverage.json
    """
    logger = get_logger(__name__)

    # 1. Load and concatenate raw CSVs
    csv_paths = _load_raw_csv_files()
    logger.info(f"Found {len(csv_paths)} raw CSV file(s) to process.")

    data_frames: List[pd.DataFrame] = []
    for csv_path in csv_paths:
        logger.info(f"Loading raw data from {csv_path}")
        # Read everything as string first – unit conversion will coerce as needed
        df_raw = pd.read_csv(csv_path, dtype=str)

        # Load and apply unit metadata
        units = _load_units_metadata(csv_path)
        df_raw = _apply_unit_conversions(df_raw, units)

        data_frames.append(df_raw)

    if not data_frames:
        raise RuntimeError("No data frames were loaded from raw CSV files.")

    df = pd.concat(data_frames, ignore_index=True)

    # 2. Compute field coverage BEFORE any imputation
    field_coverage = _compute_field_coverage(df)
    coverage_path = paths.data("cleaned", "field_coverage.json")
    coverage_path.parent.mkdir(parents=True, exist_ok=True)
    with coverage_path.open("w", encoding="utf-8") as f:
        json.dump(field_coverage, f, indent=2)
    logger.info(f"Field coverage written to {coverage_path}")

    # 3. Canonicalise treatment_type
    df = _canonicalise_treatment_type(df)

    # 4. Ensure numeric columns have proper dtypes (coerce errors to NaN)
    for col in REQUIRED_NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            # If a required column is missing entirely, create it filled with NaNs
            df[col] = np.nan
            logger.warning(f"Required numeric column '{col}' was missing; created with NaNs.")

    # 5. Median impute missing numeric values per substrate class (pair_id)
    if "pair_id" not in df.columns:
        raise RuntimeError("Column ``pair_id`` is required for per‑class imputation but is missing.")
    df, impute_log = _median_impute_per_class(
        df, class_col="pair_id", numeric_cols=REQUIRED_NUMERIC_COLUMNS
    )
    impute_path = paths.data("cleaned", "imputation_log.json")
    impute_path.parent.mkdir(parents=True, exist_ok=True)
    with impute_path.open("w", encoding="utf-8") as f:
        json.dump(impute_log, f, indent=2)
    logger.info(f"Imputation log written to {impute_path}")

    # 6. One‑hot encode categorical columns (treatment_type and pair_id)
    categorical_cols = ["treatment_type", "pair_id"]
    df = _one_hot_encode(df, categorical_cols)

    # 7. Final sanity check – no missing values should remain
    if df.isna().any().any():
        missing_summary = df.isna().sum()
        raise RuntimeError(
            f"Missing values remain after imputation:\\n{missing_summary}"
        )
    else:
        logger.info("All missing values successfully imputed.")

    # 8. Write cleaned CSV
    cleaned_path = paths.data("cleaned", "cleaned.csv")
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cleaned_path, index=False)
    logger.info(f"Cleaned dataset written to {cleaned_path}")

    logger.info("Pre‑processing completed successfully.")

if __name__ == "__main__":
    main()
