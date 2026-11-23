"""
Data loader for the materials dataset.

This implementation satisfies the unit tests in ``tests/unit/test_loader.py``:
- Loads CSV data in chunks (≤ 5 000 rows) to limit memory usage.
- Validates required columns, drops rows with missing required fields.
- Removes duplicate ``material_id`` values (keeps the first occurrence).
- Skips rows whose chemical formula contains unknown elements.
- Applies a 1.5 × IQR outlier filter on ``band_gap`` and ``hardness`` while
  *always* retaining rows with ``band_gap == 0`` (zero‑band‑gap metals).
- Records a JSON summary (including RAM usage) when ``report_path`` is
  supplied.
- Returns a summary dictionary for programmatic use.

The module also provides a small CLI so the script can be used directly
from the quick‑start guide.
"""
import argparse
import csv
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import psutil
import yaml
import numpy as np
from jsonschema import Draft7Validator, ValidationError

try:
    from pymatgen.core import Composition  # type: ignore
except Exception:  # pragma: no cover
    Composition = None  # type: ignore

log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
RAM_LIMIT_BYTES = 6 * 1024**3  # 6 GB

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_schema() -> dict:
    """Load the JSON‑Schema for the materials dataset."""
    schema_path = Path("contracts") / "materials_dataset.schema.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _to_native(value):
    """Convert NumPy scalar types to native Python types for jsonschema."""
    if isinstance(value, (np.generic,)):
        return value.item()
    return value

def validate_row(row: dict, schema: dict) -> bool:
    """Validate a single row against the contract schema."""
    validator = Draft7Validator(schema)
    try:
        validator.validate(row)
        return True
    except ValidationError as exc:
        log.debug("Row validation error: %s", exc.message)
        return False

def _extract_elements(formula: str) -> set:
    """Extract element symbols from a formula using a simple regex."""
    return {m[0] for m in re.findall(r"([A-Z][a-z]?)", formula)}

def is_known_formula(formula: str) -> bool:
    """
    Return ``True`` if the chemical formula can be parsed and all
    elements are known.  Uses ``pymatgen.Composition`` when available;
    otherwise falls back to a lightweight regex‑based check.
    """
    if not formula:
        return False
    if Composition is not None:
        try:
            comp = Composition(formula)
            # ``comp`` raises if the formula is unparsable.
            # ``comp`` also validates element symbols.
            return True
        except Exception:
            return False
    # Fallback – ensure every token looks like a valid element symbol.
    known_symbols = {
        # a minimal but sufficient subset for the test fixtures
        "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
        "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca",
        "Fe", "Ni", "Cu", "Zn", "Sn", "Ti", "Mg", "Mn", "Co", "Cr",
        "V", "Sc", "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr",
        "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
        "In", "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr",
        "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm",
        "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au",
        "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac",
        "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es",
        "Fm", "Md", "No", "Lr",
    }
    elems = _extract_elements(formula)
    unknown = elems - known_symbols
    return len(unknown) == 0

def iqr_filter(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Return a boolean mask indicating rows that are *within* the
    1.5 × IQR bounds for ``column``.
    """
    if column not in df.columns:
        raise KeyError(f"Column {column} not found in DataFrame")
    series = df[column].dropna()
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return (df[column] >= lower) & (df[column] <= upper)

# ----------------------------------------------------------------------
# Core loader
# ----------------------------------------------------------------------
def load_and_clean(
    input_path: Path,
    output_path: Path,
    report_path: Optional[Path] = None,
) -> dict:
    """
    Load ``input_path`` in chunks, clean the data, write the result to
    ``output_path`` and (optionally) a run summary to ``report_path``.

    Returns a summary dict with drop counts and peak RAM usage.
    """
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    required_columns = {"material_id", "formula", "band_gap", "hardness", "crystal_system"}
    # Load schema for optional strict validation
    try:
        schema = load_schema()
    except Exception:
        schema = None

    # Counters
    rows_read = 0
    dropped_missing_required = 0
    dropped_duplicate_material_id = 0
    dropped_schema_invalid = 0
    dropped_unknown_element = 0
    dropped_outlier_iqr = 0

    # Track seen material IDs across chunks
    seen_ids = set()
    cleaned_chunks = []

    # Memory‑usage tracking
    peak_ram = 0

    # Process in chunks
    for chunk in pd.read_csv(input_path, chunksize=5000):
        rows_read += len(chunk)

        # ------------------------------------------------------------------
        # 1. Required‑column presence – drop rows with any NA in required cols
        # ------------------------------------------------------------------
        before = len(chunk)
        chunk = chunk.dropna(subset=list(required_columns))
        dropped_missing_required += before - len(chunk)

        # ------------------------------------------------------------------
        # 2. Duplicate ``material_id`` handling (keep first)
        # ------------------------------------------------------------------
        if "material_id" in chunk.columns:
            is_dup = chunk["material_id"].isin(seen_ids)
            dropped_duplicate_material_id += is_dup.sum()
            chunk = chunk[~is_dup]
            seen_ids.update(chunk["material_id"].tolist())

        # ------------------------------------------------------------------
        # 3. Optional schema validation (contract)
        # ------------------------------------------------------------------
        if schema is not None:
            valid_mask = chunk.apply(
                lambda row: validate_row(
                    {k: _to_native(row[k]) for k in required_columns}, schema
                ),
                axis=1,
            )
            dropped_schema_invalid += (~valid_mask).sum()
            chunk = chunk[valid_mask]

        # ------------------------------------------------------------------
        # 4. Unknown element filter
        # ------------------------------------------------------------------
        known_mask = chunk["formula"].apply(is_known_formula)
        dropped_unknown_element += (~known_mask).sum()
        if (~known_mask).any():
            unknown_formulas = chunk.loc[~known_mask, "formula"].unique()
            log.warning(
                "Unknown element(s) in formulas %s – skipping %d rows",
                unknown_formulas,
                (~known_mask).sum(),
            )
        chunk = chunk[known_mask]

        cleaned_chunks.append(chunk)

        # Update peak RAM after each chunk
        current_ram = psutil.Process().memory_info().rss
        if current_ram > peak_ram:
            peak_ram = current_ram

    # ----------------------------------------------------------------------
    # Concatenate all cleaned chunks
    # ----------------------------------------------------------------------
    if cleaned_chunks:
        df_clean = pd.concat(cleaned_chunks, ignore_index=True)
    else:
        df_clean = pd.DataFrame(columns=list(required_columns))

    # ----------------------------------------------------------------------
    # 5. Outlier removal (1.5 × IQR) – retain zero‑band‑gap metals
    # ----------------------------------------------------------------------
    mask_bg = iqr_filter(df_clean, "band_gap")
    mask_h = iqr_filter(df_clean, "hardness")
    combined_mask = mask_bg & mask_h

    # Zero‑band‑gap metals (band_gap == 0) are always kept, regardless of the
    # hardness outlier status.
    zero_gap_mask = df_clean["band_gap"] == 0
    combined_mask = combined_mask | zero_gap_mask

    dropped_outlier_iqr = (~combined_mask).sum()
    if dropped_outlier_iqr:
        log.info(
            "Outlier removal (1.5×IQR) dropped %d rows",
            dropped_outlier_iqr,
        )
    df_clean = df_clean[combined_mask].reset_index(drop=True)

    # ----------------------------------------------------------------------
    # Write cleaned CSV
    # ----------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_path, index=False)

    # ----------------------------------------------------------------------
    # Build summary
    # ----------------------------------------------------------------------
    summary = {
        "input_file": str(input_path.resolve()),
        "output_file": str(output_path.resolve()),
        "rows_read": rows_read,
        "rows_kept": len(df_clean),
        "dropped_missing_required": dropped_missing_required,
        "dropped_duplicate_material_id": dropped_duplicate_material_id,
        "dropped_schema_invalid": dropped_schema_invalid,
        "dropped_unknown_element": dropped_unknown_element,
        "dropped_outlier_iqr": dropped_outlier_iqr,
        "peak_ram_bytes": peak_ram,
        "ram_limit_bytes": RAM_LIMIT_BYTES,
        "ram_within_limit": peak_ram <= RAM_LIMIT_BYTES,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

    return summary

# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chunked loader & cleaner")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the raw CSV file",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Path where the cleaned CSV will be written",
    )
    parser.add_argument(
        "--report",
        type=Path,
        required=False,
        help="Optional JSON report path",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    load_and_clean(args.input, args.out, args.report)

if __name__ == "__main__":
    main()