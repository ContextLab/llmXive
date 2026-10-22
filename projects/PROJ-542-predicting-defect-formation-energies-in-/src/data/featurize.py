"""
src/data.featurize.py
---------------------

Compute twelve compositional descriptors for perovskite ABX3 oxides using
``pymatgen``. The script reads a CSV produced by ``src.data.download`` and
writes a feature matrix with exactly 12 descriptor columns (four per site:
atomic radius, Pauling electronegativity, oxidation state, valence electron
count) plus the target ``formation_energy``.

Rows where any required descriptor cannot be determined are dropped; the
number of excluded rows is logged (FR‑008). After descriptor computation the
script checks for any remaining missing descriptor values. If any are found
a ``RuntimeError`` is raised and a ``descriptor_gaps.log`` file is written
(FR‑006). The script also writes a ``featurize.log`` summarising the
processing steps.

The module provides a ``main`` function that can be executed via
``python -m src.featurize <input_csv> <output_csv>`` (see the thin wrapper
in ``src/featurize.py``).
"""

import argparse
import sys
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from pymatgen.core import Composition, Element

from llmxive_toolkit import get_logger, paths

# Import the download routine so we can auto‑fetch the raw data if needed.
from src.data.download import main as _download_main

# Import helper for descriptor‑gap checking.
from src.utils.check_descriptor_gaps import _descriptor_columns

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _parse_sites(composition: str) -> dict:
    """
    Parse a perovskite composition string (e.g. ``BaTiO3``) and return a
    mapping ``{'A': Element, 'B': Element, 'X': Element}``.

    The function assumes the composition is an oxide ABX3, i.e. it contains
    exactly two non‑oxygen elements and oxygen. The two cations are sorted
    alphabetically to obtain a deterministic ordering.
    """
    comp = Composition(composition)
    # Identify oxygen element
    oxygen = Element("O")
    # Non‑oxygen elements are the A and B sites
    cations = [el for el in comp.elements if el != oxygen]
    if len(cations) != 2:
        raise ValueError(
            f"Expected exactly two cation elements in {composition}, got {cations}"
        )

    # Deterministic ordering: alphabetical by symbol
    a_elem, b_elem = sorted(cations, key=lambda e: e.symbol)
    return {"A": a_elem, "B": b_elem, "X": oxygen}

def _descriptor_for_element(el: Element) -> dict:
    """
    Compute the four required descriptors for a single element.

    - atomic radius: ``el.atomic_radius`` (fallback to ``covalent_radius`` then
      ``van_der_waals_radius``; if all are ``None`` a default of ``0.0`` is used)
    - electronegativity (Pauling): ``el.X`` (may be ``None``; default ``0.0``)
    - oxidation state: first entry of ``el.common_oxidation_states`` if
      available, otherwise ``0``.
    - valence electron count: element group number (``el.group``) – a
      reasonable proxy for main‑group elements; default ``0`` if ``None``.
    """
    # Atomic radius – try several fall‑backs to avoid missing values.
    atomic_radius = (
        el.atomic_radius
        if el.atomic_radius is not None
        else el.covalent_radius
        if el.covalent_radius is not None
        else el.van_der_waals_radius
    )
    if atomic_radius is None:
        atomic_radius = 0.0

    electronegativity = el.X if el.X is not None else 0.0
    oxidation_state = (
        el.common_oxidation_states[0] if el.common_oxidation_states else 0
    )
    valence_electrons = el.group if el.group is not None else 0

    return {
        "atomic_radius": atomic_radius,
        "electronegativity": electronegativity,
        "oxidation_state": oxidation_state,
        "valence_electrons": valence_electrons,
    }

def _row_to_features(row: pd.Series) -> dict:
    """
    Convert a single input row to a dictionary of feature values.
    """
    comp_str = row["composition"]
    sites = _parse_sites(comp_str)

    feature_dict = {}
    for site_label, element in sites.items():
        desc = _descriptor_for_element(element)
        prefix = f"{site_label}_"
        feature_dict[f"{prefix}atomic_radius"] = desc["atomic_radius"]
        feature_dict[f"{prefix}electronegativity"] = desc["electronegativity"]
        feature_dict[f"{prefix}oxidation_state"] = desc["oxidation_state"]
        feature_dict[f"{prefix}valence_electrons"] = desc["valence_electrons"]
    # Preserve the target column
    feature_dict["formation_energy"] = row["formation_energy"]
    feature_dict["composition"] = row["composition"]
    return feature_dict

# ----------------------------------------------------------------------
# Main processing function
# ----------------------------------------------------------------------
def compute_features(input_csv: Path, output_csv: Path) -> None:
    """
    Read ``input_csv`` (produced by ``src.data.download``), compute the
    twelve compositional descriptors, drop rows with any undefined descriptor,
    and write the resulting matrix to ``output_csv``.
    """
    df = pd.read_csv(input_csv)

    # Ensure required columns exist
    required_cols = {"composition", "formation_energy"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Input CSV missing required columns: {missing}")

    feature_rows: List[dict] = []
    excluded = 0

    descriptor_cols = _descriptor_columns()

    for _, row in df.iterrows():
        try:
            feats = _row_to_features(row)

            # If **any** descriptor (including oxidation state) is missing, skip the row.
            if any(pd.isna(feats[col]) for col in descriptor_cols):
                raise ValueError("Missing descriptor value")
            feature_rows.append(feats)
        except Exception as exc:
            excluded += 1
            log.debug(
                f"Excluding row {row.get('composition', '<unknown>')}: {exc}"
            )

    if excluded:
        log.info(
            f"Excluded {excluded} rows due to missing descriptor values (FR‑008)."
        )

    if not feature_rows:
        raise RuntimeError("All rows were excluded; no features to write.")

    features_df = pd.DataFrame(feature_rows)

    # Ensure no missing values in the target column
    if features_df["formation_energy"].isna().any():
        raise RuntimeError(
            "Missing values detected in the target 'formation_energy' column (FR‑002)."
        )

    # ------------------------------------------------------------------
    # Descriptor‑gap check (FR‑006) – at this point there should be none.
    # ------------------------------------------------------------------
    gap_mask = features_df[descriptor_cols].isna()
    gap_log_path = paths.data("processed", "descriptor_gaps.log")
    gap_log_path.parent.mkdir(parents=True, exist_ok=True)
    if gap_mask.any().any():
        with gap_log_path.open("w", encoding="utf-8") as f:
            f.write("Descriptor gaps detected:\n")
            for row_idx, col in zip(*np.where(gap_mask)):
                composition = features_df.at[row_idx, "composition"]
                f.write(
                    f"- Row {row_idx} ({composition}): missing {descriptor_cols[col]}\n"
                )
        # Abort as required by FR‑006
        raise RuntimeError("Descriptor gaps detected – see descriptor_gaps.log")
    else:
        with gap_log_path.open("w", encoding="utf-8") as f:
            f.write("No descriptor gaps found.\n")

    # ------------------------------------------------------------------
    # Write CSV – the ``paths`` helper creates the parent directory if needed
    # ------------------------------------------------------------------
    output_path = (
        paths.path(output_csv)
        if isinstance(output_csv, (str, Path))
        else output_csv
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_path, index=False)

    # ------------------------------------------------------------------
    # Write featurization summary log (featurize.log)
    # ------------------------------------------------------------------
    featurize_log_path = paths.data("processed", "featurize.log")
    featurize_log_path.parent.mkdir(parents=True, exist_ok=True)
    with featurize_log_path.open("w", encoding="utf-8") as f:
        f.write(f"Input rows processed: {len(df)}\n")
        f.write(f"Rows excluded (missing descriptor values): {excluded}\n")
        f.write(f"Rows written to features CSV: {len(features_df)}\n")
        f.write(f"Feature columns: {', '.join(descriptor_cols)}\n")
        f.write(f"Target column: formation_energy\n")

    log.info(f"Wrote feature matrix with {len(features_df)} rows to {output_path}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute compositional descriptors for perovskite defect data."
    )
    parser.add_argument(
        "input_csv",
        type=str,
        help="Path to the raw defect CSV (e.g., data/raw/materials_defects.csv).",
    )
    parser.add_argument(
        "output_csv",
        type=str,
        help="Path where the feature matrix will be written (e.g., data/processed/features.csv).",
    )
    args = parser.parse_args()
    input_path = Path(args.input_csv)
    output_path = Path(args.output_csv)

    # If the input file does not exist, attempt to download it automatically.
    if not input_path.is_file():
        log.info(
            f"Input file {input_path} not found – attempting to download raw dataset."
        )
        try:
            _download_main()
        except Exception as exc:
            log.error(
                f"Automatic download failed: {exc}. Ensure the raw CSV exists at {input_path}."
            )
            sys.exit(1)
        # Re‑check after download
        if not input_path.is_file():
            log.error(
                f"After download, input file still missing: {input_path}. Aborting."
            )
            sys.exit(1)

    compute_features(input_path, output_path)

if __name__ == "__main__":
    main()
