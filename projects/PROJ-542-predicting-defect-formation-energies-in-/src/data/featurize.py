"""
src/data/featurize.py
---------------------

Implements the feature engineering step for the perovskite defect
formation‑energy pipeline.  For each raw entry the script parses the
composition, extracts twelve compositional descriptors (atomic radius,
Pauling electronegativity, oxidation state, valence‑electron count for the
A, B, and X sites) using ``pymatgen``, drops rows where an oxidation state
cannot be determined, writes the feature matrix, logs the number of
dropped rows, validates that no descriptor gaps remain, and finally writes
a SHA‑256 checksum for the output CSV.
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple, List, Dict, Optional

import pandas as pd
from pymatgen.core.periodic_table import Element

from llmxive_toolkit import get_logger, paths
from src.utils.check_descriptor_gaps import check_descriptor_gaps
from src.utils.checksum import write_checksum

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _site_descriptors(elem: Element) -> Tuple[Optional[float], Optional[float], Optional[int], Optional[int]]:
    """
    Return the four required descriptors for a given element.

    Returns
    -------
    radius : float | None
        Covalent atomic radius (Å). ``Element.atomic_radius`` may be ``None``.
    electronegativity : float | None
        Pauling electronegativity (``Element.X``). May be ``None``.
    oxidation_state : int | None
        The *most common* oxidation state for the element. If the element
        provides no oxidation‑state list, ``None`` is returned.
    valence_electrons : int | None
        Number of valence electrons (``Element.valence_electrons``). May be ``None``.
    """
    radius = getattr(elem, "atomic_radius", None)
    electronegativity = getattr(elem, "X", None)

    # Choose the first oxidation state if the list exists; otherwise None.
    ox_states = getattr(elem, "oxidation_states", [])
    oxidation_state = ox_states[0] if ox_states else None

    valence = getattr(elem, "valence_electrons", None)

    return radius, electronegativity, oxidation_state, valence


def _parse_perovskite(composition: str) -> Tuple[Element, Element, Element]:
    """
    Very simple parser for ABX₃ formulas.

    - If the formula contains oxygen (``O``) we treat it as the X site.
    - The remaining two distinct elements are assigned to A and B
      (alphabetical order to keep the operation deterministic).

    Parameters
    ----------
    composition : str
        Chemical formula string, e.g. ``BaTiO3``.

    Returns
    -------
    (A, B, X) : tuple of ``Element`` objects

    Raises
    ------
    ValueError
        If the formula does not contain exactly three distinct
        elements (including oxygen) or if any element symbol cannot be
        resolved by ``pymatgen``.
    """
    # Extract element symbols using a regular expression.
    import re

    symbols = re.findall(r"[A-Z][a-z]?", composition)
    if not symbols:
        raise ValueError(f"Unable to parse composition: {composition}")

    unique = sorted(set(symbols))
    if "O" not in unique:
        raise ValueError(f"Composition does not contain oxygen (expected perovskite): {composition}")

    # X is oxygen.
    X = Element("O")

    # Remove oxygen and ensure exactly two remaining distinct elements.
    non_o = [s for s in unique if s != "O"]
    if len(non_o) != 2:
        raise ValueError(f"Expected two non‑oxygen elements in perovskite formula: {composition}")

    A_sym, B_sym = sorted(non_o)  # alphabetical order → deterministic
    A = Element(A_sym)
    B = Element(B_sym)
    return A, B, X


def _build_feature_row(row: pd.Series) -> Optional[Dict[str, any]]:
    """
    Build a dictionary with the twelve descriptor columns for a single
    raw data row.

    If any descriptor cannot be obtained (e.g. missing oxidation state),
    ``None`` is returned so the caller can decide to drop the row.

    Returns
    -------
    dict | None
        Mapping from column name to value, or ``None`` if the row should be
        omitted.
    """
    try:
        A, B, X = _parse_perovskite(row["composition"])
    except Exception as exc:
        log.warning(f"Failed to parse composition '{row['composition']}': {exc}")
        return None

    # Gather descriptors for each site.
    descriptors = {}
    for site, elem in zip(("A", "B", "X"), (A, B, X)):
        radius, eneg, ox_state, val_e = _site_descriptors(elem)

        # If oxidation state is missing we treat the whole row as invalid.
        if ox_state is None:
            return None

        descriptors[f"{site}_atomic_radius"] = radius
        descriptors[f"{site}_electronegativity"] = eneg
        descriptors[f"{site}_oxidation_state"] = ox_state
        descriptors[f"{site}_valence_electrons"] = val_e

    # Add the target value.
    descriptors["formation_energy"] = row["formation_energy"]
    return descriptors

# ----------------------------------------------------------------------
# Core implementation
# ----------------------------------------------------------------------


def compute_features(input_csv: Path, output_csv: Path) -> None:
    """
    Reads ``input_csv`` (the raw defect CSV), computes the twelve
    compositional descriptors, drops rows with any missing descriptor,
    writes the resulting feature matrix to ``output_csv``, runs the
    descriptor‑gap checker (which aborts on gaps), and finally writes a
    SHA‑256 checksum for the output CSV.

    Parameters
    ----------
    input_csv : Path
        Path to the raw dataset produced by ``src.data.download``.
    output_csv : Path
        Destination for the processed feature matrix.
    """
    # ------------------------------------------------------------------
    # Load raw data.
    # ------------------------------------------------------------------
    raw_df = pd.read_csv(input_csv)
    if "composition" not in raw_df.columns or "formation_energy" not in raw_df.columns:
        raise RuntimeError("Input CSV must contain 'composition' and 'formation_energy' columns")

    # ------------------------------------------------------------------
    # Compute features.
    # ------------------------------------------------------------------
    feature_rows: List[Dict[str, any]] = []
    dropped_due_to_ox = 0

    for _, row in raw_df.iterrows():
        feature_dict = _build_feature_row(row)
        if feature_dict is None:
            dropped_due_to_ox += 1
            continue
        feature_rows.append(feature_dict)

    # ------------------------------------------------------------------
    # Write featurization log.
    # ------------------------------------------------------------------
    featurize_log_path = paths.data("processed", "featurize.log")
    featurize_log_path.parent.mkdir(parents=True, exist_ok=True)
    with featurize_log_path.open("w") as log_f:
        log_f.write(f"Dropped rows due to missing oxidation state: {dropped_due_to_ox}\\n")
    log.info(f"Featurization log written to {featurize_log_path}")

    # ------------------------------------------------------------------
    # Build DataFrame and write CSV.
    # ------------------------------------------------------------------
    if not feature_rows:
        raise RuntimeError("No rows survived featurization – all rows dropped.")

    features_df = pd.DataFrame(feature_rows)

    # Ensure the output directory exists.
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_csv, index=False)
    log.info(f"Feature matrix written to {output_csv}")

    # ------------------------------------------------------------------
    # Descriptor‑gap check – aborts if any descriptor is missing.
    # ------------------------------------------------------------------
    try:
        check_descriptor_gaps(features_path=output_csv)
    except RuntimeError as exc:
        # The checker already writes a detailed log; we re‑raise with the
        # required message format.
        raise RuntimeError("Descriptor gaps detected – see descriptor_gaps.log") from exc

    # ------------------------------------------------------------------
    # Compute and write checksum.
    # ------------------------------------------------------------------
    write_checksum(output_csv, paths.data("checksums"))
    log.info("Checksum for features CSV written.")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def main() -> None:
    """
    CLI wrapper used by ``python -m src.data.featurize``.

    Expected positional arguments:
        1. Path to the raw CSV (input)
        2. Path to the output features CSV (output)
    """
    parser = argparse.ArgumentParser(
        description="Compute compositional descriptors for perovskite defect data."
    )
    parser.add_argument("input_csv", type=Path, help="Path to the raw dataset CSV")
    parser.add_argument("output_csv", type=Path, help="Path where the feature matrix will be written")
    args = parser.parse_args()

    try:
        compute_features(args.input_csv, args.output_csv)
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)
