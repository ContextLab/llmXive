"""
Feature Engineering Script
==========================

This script reads the raw perovskite dataset produced by ``code/data_ingestion.py``,
computes compositional descriptors for each entry, and writes the results to
``data/processed/descriptors.csv``.

The descriptors include:

* **Atomic fractions** for every element present in the formula.
* **Weighted averages** of four elemental properties:
  - Ionic radius (Å) – average of the smallest available ionic radius for the element.
  - Pauling electronegativity.
  - Standard formation enthalpy (kJ/mol) – set to 0 for pure elements (no
    readily‑available reference in pymatgen).
  - First ionization energy (eV) – taken from ``Element.ionization_energies[0]``.
* **Variance metrics** for the same four properties, using the atomic fractions as
  weights.

The script is deliberately self‑contained and only relies on the public API
exposed by the project's ``utils`` package and the ``pymatgen`` library.
"""

import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
from pymatgen.core import Element, Composition

# Import the formula parsing helper from the utils package.
from utils.formula_parser import parse_formula, FormulaParseError

# Configure a simple logger.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Helper functions for elemental properties
# -------------------------------------------------------------------------

def _first_ionization_energy(el: Element) -> float | None:
    """Return the first ionization energy (eV) for an element, or ``None``."""
    try:
        return float(el.ionization_energies[0])
    except (AttributeError, IndexError):
        return None

def _electronegativity(el: Element) -> float | None:
    """Return the Pauling electronegativity (X) for an element, or ``None``."""
    # ``Element.X`` is the Pauling electronegativity; it may be ``None`` for
    # elements like noble gases.
    return getattr(el, "X", None)

def _ionic_radius(el: Element) -> float | None:
    """
    Return a representative ionic radius (Å) for the element.

    ``Element.ionic_radii`` is a dictionary keyed by oxidation state.
    We take the smallest radius available (most common for perovskites)
    and ignore the oxidation‑state information.
    """
    radii = getattr(el, "ionic_radii", {})
    if not radii:
        return None
    # ``radii`` maps oxidation state -> radius (Å). Choose the smallest.
    return min(radii.values())

def _formation_enthalpy(el: Element) -> float:
    """
    Return a formation enthalpy proxy (kJ/mol).

    For pure elements the standard formation enthalpy is defined as 0.
    A more sophisticated implementation would query Materials Project,
    but that would require API access. We therefore return 0 for all
    elements to keep the pipeline functional and deterministic.
    """
    return 0.0

# -------------------------------------------------------------------------
# Core descriptor computation
# -------------------------------------------------------------------------

def compute_descriptors(formula: str) -> Dict[str, float]:
    """
    Compute all required descriptors for a single chemical formula.

    Parameters
    ----------
    formula : str
        The chemical formula (e.g., ``"CsPbI3"``).

    Returns
    -------
    dict
        Mapping from descriptor name to numeric value. Keys include:

        - ``atomic_fraction_<El>`` for each element present.
        - ``weighted_ionic_radius``, ``weighted_electronegativity``,
          ``weighted_formation_enthalpy``, ``weighted_first_ionization_energy``.
        - ``variance_ionic_radius``, ``variance_electronegativity``,
          ``variance_formation_enthalpy``, ``variance_first_ionization_energy``.
    """
    try:
        # ``parse_formula`` returns a ``pymatgen.core.Composition`` object.
        comp: Composition = parse_formula(formula)
    except FormulaParseError as exc:
        logger.error("Failed to parse formula %s: %s", formula, exc)
        raise

    # Atomic fractions for each element in the composition.
    fractions: Dict[Element, float] = {
        el: comp.get_atomic_fraction(el) for el in comp.elements
    }

    # Prepare containers for property values.
    prop_vals: Dict[str, List[float]] = {
        "ionic_radius": [],
        "electronegativity": [],
        "formation_enthalpy": [],
        "first_ionization_energy": [],
    }
    prop_weights: List[float] = []

    # Build descriptor dictionary.
    descriptor: Dict[str, float] = {}

    for el, frac in fractions.items():
        # Record atomic fraction column.
        descriptor[f"atomic_fraction_{el.symbol}"] = frac

        # Gather property values (skip ``None`` entries).
        ir = _ionic_radius(el)
        en = _electronegativity(el)
        fe = _formation_enthalpy(el)
        ie = _first_ionization_energy(el)

        # Store values; ``None`` is represented by ``float('nan')`` later.
        prop_vals["ionic_radius"].append(ir if ir is not None else float("nan"))
        prop_vals["electronegativity"].append(en if en is not None else float("nan"))
        prop_vals["formation_enthalpy"].append(fe)
        prop_vals["first_ionization_energy"].append(ie if ie is not None else float("nan"))

        prop_weights.append(frac)

    # Helper to compute weighted average ignoring NaNs.
    def weighted_average(values: List[float], weights: List[float]) -> float:
        import math
        # Filter out NaNs.
        filtered = [(v, w) for v, w in zip(values, weights) if not math.isnan(v)]
        if not filtered:
            return float("nan")
        vals, wts = zip(*filtered)
        total_w = sum(wts)
        return sum(v * w for v, w in zip(vals, wts)) / total_w

    # Helper to compute weighted variance ignoring NaNs.
    def weighted_variance(values: List[float], weights: List[float], mean: float) -> float:
        import math
        filtered = [(v, w) for v, w in zip(values, weights) if not math.isnan(v)]
        if not filtered:
            return float("nan")
        vals, wts = zip(*filtered)
        total_w = sum(wts)
        return sum(w * (v - mean) ** 2 for v, w in zip(vals, wts)) / total_w

    # Compute weighted averages and variances for each property.
    for prop in prop_vals.keys():
        avg = weighted_average(prop_vals[prop], prop_weights)
        var = weighted_variance(prop_vals[prop], prop_weights, avg)
        descriptor[f"weighted_{prop}"] = avg
        descriptor[f"variance_{prop}"] = var

    return descriptor

# -------------------------------------------------------------------------
# Main execution routine
# -------------------------------------------------------------------------

def main() -> None:
    """
    Entry point for the script.

    Reads ``data/raw/nrel_perovskites.csv`` (generated by ``data_ingestion.py``,
    must contain at least a ``formula`` column and optionally ``T_d``),
    computes descriptors for every row, and writes the enriched table to
    ``data/processed/descriptors.csv``.
    """
    raw_path = Path("data/raw/nrel_perovskites.csv")
    if not raw_path.is_file():
        logger.error("Raw data file not found: %s", raw_path)
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")

    logger.info("Loading raw data from %s", raw_path)
    raw_df = pd.read_csv(raw_path)

    # Verify required columns.
    if "formula" not in raw_df.columns:
        logger.error("Input CSV must contain a 'formula' column.")
        raise KeyError("Input CSV must contain a 'formula' column.")

    # Prepare a list to collect descriptor rows.
    descriptor_rows: List[Dict[str, float]] = []

    for idx, row in raw_df.iterrows():
        formula = row["formula"]
        logger.debug("Processing formula %s (row %d)", formula, idx)

        try:
            desc = compute_descriptors(str(formula))
        except Exception as exc:
            logger.warning("Skipping formula %s due to error: %s", formula, exc)
            continue

        # Preserve original columns (e.g., T_d) in the output.
        for col in raw_df.columns:
            if col != "formula":
                desc[col] = row[col]

        # Keep the formula itself.
        desc["formula"] = formula

        descriptor_rows.append(desc)

    if not descriptor_rows:
        logger.error("No descriptors were generated – check input data.")
        raise RuntimeError("Descriptor generation failed for all rows.")

    # Create DataFrame; pandas will automatically align columns.
    descriptors_df = pd.DataFrame(descriptor_rows)

    # Ensure deterministic column order: formula first, then original columns,
    # then atomic fractions (sorted alphabetically), then weighted/variance metrics.
    original_cols = [c for c in raw_df.columns if c != "formula"]
    atomic_frac_cols = sorted([c for c in descriptors_df.columns if c.startswith("atomic_fraction_")])
    weighted_cols = sorted([c for c in descriptors_df.columns if c.startswith("weighted_")])
    variance_cols = sorted([c for c in descriptors_df.columns if c.startswith("variance_")])

    ordered_cols = (
        ["formula"]
        + original_cols
        + atomic_frac_cols
        + weighted_cols
        + variance_cols
    )
    descriptors_df = descriptors_df[ordered_cols]

    # Write output.
    output_path = Path("data/processed/descriptors.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptors_df.to_csv(output_path, index=False)
    logger.info("Descriptors written to %s (%d rows)", output_path, len(descriptors_df))

if __name__ == "__main__":
    main()
