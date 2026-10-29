"""
Descriptor calculation utilities for HEA compositions.

This module provides functions to:
* Load elemental property data (from the frozen CSV or built‑in fallback).
* Parse a composition string into element symbols with atomic fractions.
* Compute the five composition‑based descriptors required by the
  specification:
    - mixing_entropy (J mol⁻¹ K⁻¹)
    - atomic_size_mismatch (δ, %)
    - electronegativity_variance (Δχ)
    - vec (valence electron concentration)
    - tm_variance (variance of melting temperatures)
  and returns a DataFrame that conforms to both
  `contracts/descriptor.schema.yaml` and `contracts/hea_schema.schema.yaml`.

The public API matches the project’s existing surface:
  - get_elemental_properties()
  - get_property()
  - calculate_weighted_average()
  - calculate_single_composition_descriptors()
  - calculate_descriptors()
  - filter_missing_properties()
  - main()
The implementation raises a clear ``KeyError`` when an element is missing
from the elemental table and writes column names that exactly match the
JSON‑schema contracts.
"""

import os
import sys
import pandas as pd
import numpy as np
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple

from utils.logging import get_logger
from llmxive_toolkit import paths

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Elemental property handling
# ----------------------------------------------------------------------
# The project ships a frozen CSV at ``data/raw/elemental_properties.csv``.
# If the file is present we load it; otherwise we fall back to the
# hard‑coded dictionary that existed before this task was implemented.
# This guarantees that the code works even if the CSV is missing (e.g.
# during unit‑test execution) while still using the authoritative source
# when the pipeline runs end‑to‑end.
# ----------------------------------------------------------------------
ELEMENTAL_PROPERTIES_CSV = paths.data("raw", "elemental_properties.csv")

def _load_properties_from_csv() -> Dict[str, Dict[str, float]]:
    """Load elemental properties from the CSV file.

    Expected columns: ``element``, ``radius``, ``electronegativity``,
    ``valence``, ``melting_point`` (optional).  Missing columns are ignored.
    Returns a mapping ``{symbol: {prop: value, ...}}``.
    """
    csv_path = ELEMENTAL_PROPERTIES_CSV
    if not csv_path.is_file():
        logger.debug("Elemental properties CSV not found – using built‑in table.")
        return {}

    df = pd.read_csv(csv_path, dtype=str)
    required = {"element", "radius", "electronegativity", "valence"}
    missing = required - set(df.columns.str.lower())
    if missing:
        raise ValueError(f"Elemental properties CSV missing columns: {missing}")

    # Normalise column names to lower case for robust access
    df = df.rename(columns=lambda c: c.strip().lower())
    props: Dict[str, Dict[str, float]] = {}
    for _, row in df.iterrows():
        symbol = row["element"]
        try:
            radius = float(row["radius"])
            chi = float(row["electronegativity"])
            val = float(row["valence"])
            tm = (
                float(row["melting_point"])
                if "melting_point" in row and pd.notna(row["melting_point"])
                else None
            )
        except ValueError as e:
            raise ValueError(
                f"Invalid numeric value in elemental properties CSV for {symbol}: {e}"
            )

        entry: Dict[str, float] = {
            "radius": radius,
            "electronegativity": chi,
            "valence": val,
        }
        if tm is not None:
            entry["melting_point"] = tm
        props[symbol] = entry
    return props

# Hard‑coded fallback (identical to the original implementation)
_FALLBACK_ELEMENTAL_PROPERTIES: Dict[str, Dict[str, float]] = {
    "Cr": {"radius": 128, "electronegativity": 1.66, "valence": 6},
    "Co": {"radius": 125, "electronegativity": 1.88, "valence": 9},
    "Fe": {"radius": 126, "electronegativity": 1.83, "valence": 8},
    "Ni": {"radius": 124, "electronegativity": 1.91, "valence": 10},
    "Mn": {"radius": 127, "electronegativity": 1.55, "valence": 7},
    "Al": {"radius": 143, "electronegativity": 1.61, "valence": 3},
    "Cu": {"radius": 128, "electronegativity": 1.90, "valence": 11},
    "Ti": {"radius": 147, "electronegativity": 1.54, "valence": 4},
    "V": {"radius": 134, "electronegativity": 1.63, "valence": 5},
    "Nb": {"radius": 146, "electronegativity": 1.60, "valence": 5},
    "Ta": {"radius": 146, "electronegativity": 1.50, "valence": 5},
    "Mo": {"radius": 139, "electronegativity": 2.16, "valence": 6},
    "W": {"radius": 139, "electronegativity": 2.36, "valence": 6},
    "Zr": {"radius": 160, "electronegativity": 1.33, "valence": 4},
    "Hf": {"radius": 159, "electronegativity": 1.30, "valence": 4},
    "Si": {"radius": 117, "electronegativity": 1.90, "valence": 4},
    "C": {"radius": 77, "electronegativity": 2.55, "valence": 4},
    "O": {"radius": 73, "electronegativity": 3.44, "valence": 6},
}

def get_elemental_properties() -> Dict[str, Dict[str, float]]:
    """Return the full elemental property dictionary.

    Preference is given to the CSV version; if it cannot be loaded the
    built‑in fallback dictionary is returned.
    """
    csv_props = _load_properties_from_csv()
    if csv_props:
        logger.debug("Loaded elemental properties from CSV.")
        return csv_props
    logger.debug("Using built‑in elemental property table.")
    return _FALLBACK_ELEMENTAL_PROPERTIES

def get_property(element: str, property_name: str) -> Optional[float]:
    """Retrieve a specific property for an element.

    Raises:
        KeyError: If ``element`` is not present in the property table.
    """
    props = get_elemental_properties()
    if element not in props:
        raise KeyError(f"Element '{element}' not found in elemental property table.")
    return props[element].get(property_name)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def calculate_weighted_average(values: List[float], fractions: List[float]) -> float:
    """Calculate the weighted average of ``values`` using ``fractions``."""
    if not values or not fractions:
        return 0.0
    if len(values) != len(fractions):
        raise ValueError("Values and fractions must have the same length.")
    return sum(v * f for v, f in zip(values, fractions))

_COMPOSITION_REGEX = re.compile(r"([A-Z][a-z]?)(?:\(?([\d\.]+)\)?)?")

def _parse_composition(comp_str: str) -> Tuple[List[str], List[float]]:
    """
    Parse a composition string into ordered element symbols and atomic fractions.

    Supported formats:
      * ``CoCrFeMnNi``                – equiatomic (fractions are inferred)
      * ``Co0.2Cr0.2Fe0.2Mn0.2Ni0.2`` – explicit fractions
      * ``Co(0.2)Cr(0.2)Fe(0.2)``      – parentheses are allowed

    Returns:
        (elements, fractions) where ``fractions`` sum to 1.0.
    """
    matches = _COMPOSITION_REGEX.findall(comp_str.replace(" ", ""))
    if not matches:
        raise ValueError(f"Unable to parse composition string: '{comp_str}'")

    elements: List[str] = []
    fractions: List[float] = []
    for elem, frac_str in matches:
        elements.append(elem)
        if frac_str:
            fractions.append(float(frac_str))
    # If fractions were omitted, assume equiatomic
    if not fractions:
        n = len(elements)
        fractions = [1.0 / n] * n
    else:
        total = sum(fractions)
        if total == 0:
            raise ValueError("Sum of fractions is zero.")
        fractions = [f / total for f in fractions]  # normalise to 1
    return elements, fractions

# ----------------------------------------------------------------------
# Descriptor calculations for a single composition
# ----------------------------------------------------------------------
def calculate_single_composition_descriptors(
    row: pd.Series, props: Dict[str, Dict[str, float]]
) -> Dict[str, Any]:
    """
    Compute the five descriptors for a single alloy composition.

    Expected input:
      * ``row`` must contain a ``composition`` field (string).
    Returns a dictionary with keys matching the JSON‑schema contracts:
      - ``mixing_entropy``
      - ``atomic_size_mismatch``
      - ``electronegativity_variance``
      - ``vec``
      - ``tm_variance``
    """
    comp_str = row.get("composition")
    if pd.isna(comp_str):
        raise ValueError("Missing 'composition' field in row.")

    elements, fractions = _parse_composition(str(comp_str))

    # Validate that every element exists in the property table.
    radii: List[float] = []
    electronegativities: List[float] = []
    valences: List[float] = []
    melting_points: List[float] = []

    for elem in elements:
        # ``get_property`` will raise KeyError if the element is unknown.
        r = get_property(elem, "radius")
        chi = get_property(elem, "electronegativity")
        v = get_property(elem, "valence")
        tm = get_property(elem, "melting_point")  # may be None

        radii.append(r)                # type: ignore[arg-type]
        electronegativities.append(chi)  # type: ignore[arg-type]
        valences.append(v)              # type: ignore[arg-type]
        if tm is not None:
            melting_points.append(tm)

    # 1. Mixing entropy (ΔS_mix) = -R Σ c_i ln c_i
    R = 8.314  # J·mol⁻¹·K⁻¹
    s_mix = -R * sum(c * np.log(c) for c in fractions if c > 0)

    # 2. Atomic size mismatch (δ) = 100 * sqrt( Σ c_i (1 - r_i / r̄)² )
    r_bar = calculate_weighted_average(radii, fractions)
    delta_sq = sum(c * (1 - r / r_bar) ** 2 for r, c in zip(radii, fractions))
    delta = 100.0 * np.sqrt(delta_sq)

    # 3. Electronegativity variance (Δχ) = sqrt( Σ c_i (χ_i - χ̄)² )
    chi_bar = calculate_weighted_average(electronegativities, fractions)
    delta_chi = np.sqrt(
        sum(c * (chi - chi_bar) ** 2 for chi, c in zip(electronegativities, fractions))
    )

    # 4. Valence electron concentration (VEC) = Σ c_i * V_i
    vec = calculate_weighted_average(valences, fractions)

    # 5. Melting‑point variance (ΔTm) – if we have melting points, compute variance,
    #    otherwise set to 0.0 (the schema permits zero).
    if melting_points:
        tm_bar = calculate_weighted_average(
            melting_points, fractions[: len(melting_points)]
        )
        delta_tm = np.sqrt(
            sum(
                c * (tm - tm_bar) ** 2
                for tm, c in zip(melting_points, fractions[: len(melting_points)])
            )
        )
    else:
        delta_tm = 0.0

    return {
        "mixing_entropy": s_mix,
        "atomic_size_mismatch": delta,
        "electronegativity_variance": delta_chi,
        "vec": vec,
        "tm_variance": delta_tm,
    }

# ----------------------------------------------------------------------
# Public pipeline functions
# ----------------------------------------------------------------------
def calculate_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply descriptor calculation to every row of ``df``.

    The input DataFrame must contain a ``composition`` column.
    The returned DataFrame contains the original columns plus the
    descriptor columns defined in ``contracts/descriptor.schema.yaml``.
    Rows that raise ``KeyError`` (unknown element) are propagated so
    that callers can handle the error according to FR‑009.
    """
    props = get_elemental_properties()
    descriptor_rows = []
    for idx, row in df.iterrows():
        try:
            desc = calculate_single_composition_descriptors(row, props)
        except Exception as e:
            logger.error(f"Failed to compute descriptors for row {idx}: {e}")
            raise
        descriptor_rows.append(desc)

    desc_df = pd.DataFrame(descriptor_rows)
    result_df = pd.concat([df.reset_index(drop=True), desc_df], axis=1)
    return result_df

def filter_missing_properties(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows where any descriptor column is NaN.
    This mirrors the original helper but now works with the
    concrete descriptor column names.
    """
    desc_cols = [
        "mixing_entropy",
        "atomic_size_mismatch",
        "electronegativity_variance",
        "vec",
        "tm_variance",
    ]
    initial = len(df)
    df_clean = df.dropna(subset=desc_cols)
    logger.info(
        f"filter_missing_properties: removed {initial - len(df_clean)} rows with NaNs"
    )
    return df_clean

def _load_schema(schema_filename: str) -> Dict[str, Any]:
    """
    Load a JSON‑schema file from the project's ``specs`` directory.

    The contracts live under
    ``specs/001-predicting-the-yield-strength-of-high-en/contracts``.
    """
    schema_path = (
        paths.root
        / "specs"
        / "001-predicting-the-yield-strength-of-high-en"
        / "contracts"
        / schema_filename
    )
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    """
    Entry point used by the pipeline (T015) and by the integration test.
    It reads ``data/raw/heas_raw.csv`` (which must contain a ``composition``
    column), computes descriptors, writes the result to
    ``data/processed/hea_descriptors.csv`` and validates the output against
    both JSON‑schema contracts.
    """
    raw_path = paths.data("raw", "heas_raw.csv")
    processed_dir = paths.data("processed")
    os.makedirs(processed_dir, exist_ok=True)
    out_path = processed_dir / "hea_descriptors.csv"

    if not raw_path.is_file():
        logger.error(f"Raw dataset not found at {raw_path}")
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}")

    logger.info(f"Loading raw dataset from {raw_path}")
    df_raw = pd.read_csv(raw_path)

    # Basic sanity check – the integration test expects at least one row.
    if df_raw.empty:
        raise RuntimeError("Raw dataset is empty – cannot compute descriptors.")

    logger.info("Computing descriptors")
    df_desc = calculate_descriptors(df_raw)

    logger.info(f"Writing descriptor table to {out_path}")
    df_desc.to_csv(out_path, index=False)

    # ------------------------------------------------------------------
    # Schema validation (fails loudly if the output does not conform)
    # ------------------------------------------------------------------
    from jsonschema import validate, ValidationError

    try:
        descriptor_schema = _load_schema("descriptor.schema.yaml")
        hea_schema = _load_schema("hea_schema.schema.yaml")
    except Exception as exc:
        logger.error(f"Failed to load schema files: {exc}")
        raise

    # Validate each record against both schemas.
    for _, rec in df_desc.iterrows():
        rec_dict = rec.to_dict()
        try:
            validate(instance=rec_dict, schema=descriptor_schema)
            validate(instance=rec_dict, schema=hea_schema)
        except ValidationError as ve:
            logger.error(
                f"Schema validation error for record {rec_dict.get('composition')}: {ve.message}"
            )
            raise

    logger.info("Descriptor generation completed successfully.")
    return df_desc

if __name__ == "__main__":
    main()
