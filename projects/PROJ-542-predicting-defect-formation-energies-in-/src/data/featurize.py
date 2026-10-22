"""
src/data/featurize.py
---------------------

Implements the feature‑engineering step for the perovskite defect
formation‑energy pipeline.  The script reads a raw CSV produced by the
Materials Project download step, parses each composition, computes the
twelve compositional descriptors (atomic radius, Pauling electronegativity,
most‑common oxidation state, and valence‑electron count for the A, B, and X
sites), drops rows where any descriptor cannot be determined, writes the
resulting feature matrix, logs the number of dropped rows, checks for any
remaining descriptor gaps, writes a descriptor‑gap report, and finally
creates a SHA‑256 checksum for the feature CSV.

The public API mirrors the contract defined in ``code/data/featurize.py``:
  * ``compute_features(input_csv: Path, output_csv: Path) -> None``
  * ``main() -> None`` (CLI entry point)

All paths are resolved relative to the project root using the
``llmxive_toolkit.paths`` helpers, which automatically create the
necessary directories.
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import pandas as pd
from pymatgen.core.periodic_table import Element

from llmxive_toolkit import get_logger, paths
from src.utils.checksum import write_checksum

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions for descriptor extraction
# ----------------------------------------------------------------------
def _site_descriptors(
    elem: Element,
) -> Tuple[Optional[float], Optional[float], Optional[int], Optional[int]]:
    """
    Return the four required descriptors for a single element.

    Parameters
    ----------
    elem : Element
        pymatgen Element object.

    Returns
    -------
    radius : float | None
        Covalent atomic radius (Å). May be ``None``.
    electronegativity : float | None
        Pauling electronegativity. May be ``None``.
    oxidation_state : int | None
        Most common oxidation state (the first entry in
        ``elem.oxidation_states``). ``None`` if unavailable.
    valence_electrons : int | None
        Number of valence electrons. May be ``None``.
    """
    radius = elem.atomic_radius
    electronegativity = elem.X
    oxidation_state = elem.oxidation_states[0] if elem.oxidation_states else None
    valence_electrons = elem.valence_electrons
    return radius, electronegativity, oxidation_state, valence_electrons

def _parse_perovskite(composition: str) -> Tuple[Element, Element, Element]:
    """
    Very simple parser for ABX₃ formulas.

    The function assumes the formula contains oxygen (the X site) and
    exactly two other distinct elements, which are ordered alphabetically
    to obtain deterministic A / B assignment.

    Parameters
    ----------
    composition : str
        Chemical formula, e.g. ``BaTiO3``.

    Returns
    -------
    (A, B, X) : tuple of Element objects

    Raises
    ------
    ValueError
        If the formula does not contain exactly three distinct elements
        (including oxygen) or if any element symbol cannot be resolved.
    """
    # Remove whitespace and ensure uppercase/lowercase are respected.
    comp = composition.replace(" ", "")
    # Extract element symbols using pymatgen's parsing utilities.
    # For simplicity we rely on the fact that the formula is already
    # normalized (e.g. ``BaTiO3``) and contains only element symbols
    # followed by optional integer counts.
    symbols = []
    i = 0
    while i < len(comp):
        # An element symbol starts with an uppercase letter.
        if not comp[i].isupper():
            raise ValueError(f"Invalid formula '{composition}'")
        symbol = comp[i]
        i += 1
        # Optional lowercase letter.
        if i < len(comp) and comp[i].islower():
            symbol += comp[i]
            i += 1
        # Skip any numeric characters (the count).
        while i < len(comp) and comp[i].isdigit():
            i += 1
        symbols.append(symbol)

    # Identify X (oxygen) and the remaining two elements.
    unique_symbols = sorted(set(symbols))
    if "O" not in unique_symbols:
        raise ValueError(f"Oxygen not found in formula '{composition}'")
    if len(unique_symbols) != 3:
        raise ValueError(
            f"Expected 3 distinct elements (including O) in '{composition}', got {unique_symbols}"
        )
    # X is oxygen, A and B are the other two (alphabetical order).
    unique_symbols.remove("O")
    A_sym, B_sym = sorted(unique_symbols)
    try:
        A = Element(A_sym)
        B = Element(B_sym)
        X = Element("O")
    except Exception as exc:
        raise ValueError(f"Failed to resolve element symbols in '{composition}': {exc}") from exc
    return A, B, X

def _build_feature_row(row: pd.Series) -> Optional[Dict[str, Any]]:
    """
    Build a dictionary containing the twelve descriptor columns for a
    single raw data row.

    If any descriptor is ``None`` the function returns ``None`` so that
    the caller can drop the row.

    Parameters
    ----------
    row : pd.Series
        A row from the raw CSV. Must contain at least the ``composition``
        column.

    Returns
    -------
    dict | None
        Mapping from column name to descriptor value, or ``None`` if the
        row should be omitted.
    """
    try:
        A, B, X = _parse_perovskite(row["composition"])
    except Exception as exc:
        log.debug(f"Skipping composition '{row.get('composition')}' due to parse error: {exc}")
        return None

    descriptors = {}
    for site, elem in zip(("A", "B", "X"), (A, B, X)):
        radius, eneg, ox_state, val_e = _site_descriptors(elem)
        # If any descriptor is missing we drop the entire row.
        if None in (radius, eneg, ox_state, val_e):
            return None
        descriptors[f"{site}_atomic_radius"] = radius
        descriptors[f"{site}_electronegativity"] = eneg
        descriptors[f"{site}_oxidation_state"] = ox_state
        descriptors[f"{site}_valence_electrons"] = val_e

    # Preserve the target and composition columns.
    descriptors["composition"] = row["composition"]
    descriptors["formation_energy"] = row["formation_energy"]
    return descriptors

# ----------------------------------------------------------------------
# Core implementation
# ----------------------------------------------------------------------
def compute_features(input_csv: Path, output_csv: Path) -> None:
    """
    Read the raw defect CSV, compute compositional descriptors, write the
    feature matrix, log dropped rows, verify that no descriptor gaps remain,
    and write a SHA‑256 checksum for the output.

    Parameters
    ----------
    input_csv : Path
        Path to ``data/raw/materials_defects.csv`` (or a user‑provided CSV
        with the same schema).
    output_csv : Path
        Destination for ``data/processed/features.csv``.
    """
    # Resolve paths via llmxive_toolkit to guarantee directory creation.
    input_path = paths.path(input_csv)
    output_path = paths.path(output_csv)

    if not input_path.is_file():
        raise FileNotFoundError(f"Raw dataset not found at {input_path}")

    log.info(f"Reading raw dataset from {input_path}")
    raw_df = pd.read_csv(input_path)

    required_raw_cols = {"composition", "formation_energy"}
    if not required_raw_cols.issubset(set(raw_df.columns)):
        missing = required_raw_cols - set(raw_df.columns)
        raise RuntimeError(f"Raw CSV is missing required columns: {missing}")

    feature_rows = []
    dropped_count = 0
    for _, row in raw_df.iterrows():
        feature = _build_feature_row(row)
        if feature is None:
            dropped_count += 1
            continue
        feature_rows.append(feature)

    # Log how many rows were dropped because of missing descriptors.
    featurize_log_path = paths.path("data/processed/featurize.log")
    with featurize_log_path.open("w") as f_log:
        f_log.write(f"Dropped rows due to missing descriptors: {dropped_count}\n")
    log.info(f"Dropped {dropped_count} rows during featurization")

    if not feature_rows:
        raise RuntimeError("All rows were dropped – no features could be generated.")

    features_df = pd.DataFrame(feature_rows)

    # Verify that no descriptor columns contain NaN after the drop.
    descriptor_cols = [
        col
        for col in features_df.columns
        if any(col.startswith(site) for site in ("A_", "B_", "X_"))
    ]
    gaps = features_df[descriptor_cols].isnull()
    descriptor_log_path = paths.path("data/processed/descriptor_gaps.log")

    if gaps.any().any():
        # Write detailed gap information.
        with descriptor_log_path.open("w") as dlog:
            dlog.write("Descriptor gaps detected:\n")
            for idx, row in gaps.iterrows():
                missing_cols = [col for col, is_nan in row.items() if is_nan]
                if missing_cols:
                    dlog.write(f"- Row {idx} missing columns: {', '.join(missing_cols)}\n")
        raise RuntimeError("Descriptor gaps detected – see descriptor_gaps.log")
    else:
        # No gaps – write a success message.
        with descriptor_log_path.open("w") as dlog:
            dlog.write("No descriptor gaps found\n")
        log.info("No descriptor gaps detected")

    # Write the feature matrix.
    log.info(f"Writing feature matrix to {output_path}")
    features_df.to_csv(output_path, index=False)

    # Write checksum for the output CSV.
    checksum_dir = paths.path("data/checksums")
    write_checksum(output_path, checksum_dir)
    log.info(f"Checksum written to {checksum_dir}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI wrapper used by ``python -m src.data.featurize``.  Expects two
    positional arguments: the input raw CSV and the output features CSV.
    """
    parser = argparse.ArgumentParser(
        description="Compute compositional descriptors for perovskite defect data."
    )
    parser.add_argument(
        "input_csv",
        type=str,
        help="Path to the raw CSV file (e.g., data/raw/materials_defects.csv)",
    )
    parser.add_argument(
        "output_csv",
        type=str,
        help="Path where the processed features CSV will be written",
    )
    args = parser.parse_args()

    try:
        compute_features(Path(args.input_csv), Path(args.output_csv))
    except Exception as exc:
        log.error(f"Featurization failed: {exc}")
        # Propagate the exception so that the calling script sees a non‑zero exit code.
        raise