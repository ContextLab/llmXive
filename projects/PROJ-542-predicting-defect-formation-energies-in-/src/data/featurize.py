"""
src/data/featurize.py
---------------------

Computes the twelve compositional descriptors required by the
``features.schema.yaml`` contract:

    * atomic radius
    * Pauling electronegativity
    * oxidation state (first common oxidation state)
    * valence electron count

for the A, B and X sites of a perovskite ABX₃ composition.
The implementation follows the specification in T003.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from llmxive_toolkit import get_logger, paths
from pymatgen.core import Composition, Element

from src.utils.check_descriptor_gaps import check_descriptor_gaps

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
DESCRIPTOR_NAMES = [
    "atomic_radius",
    "electronegativity",
    "oxidation_state",
    "valence_electrons",
]
SITES = ["A", "B", "X"]


def _site_descriptors(elem: Element) -> Tuple[float, float, int, int]:
    """
    Return the four required descriptors for *elem*.

    If a descriptor cannot be obtained, ``None`` is returned for that
    entry – the calling code will treat it as a missing value.
    """
    # Atomic radius (Å). ``Element`` may return ``None``.
    radius = elem.atomic_radius
    # Pauling electronegativity.
    en = elem.X
    # Oxidation state – use the first common oxidation state if available.
    ox = elem.common_oxidation_states[0] if elem.common_oxidation_states else None
    # Valence electron count – ``valence`` is an integer or ``None``.
    val = elem.valence
    return radius, en, ox, val


def _parse_perovskite(composition: str) -> Tuple[Element, Element, Element]:
    """
    Very simple parser for ABX₃ formulas.

    * If the formula contains oxygen (``O``) we treat it as the X site.
    * The remaining two distinct elements are assigned to A and B
      (alphabetical order to keep the operation deterministic).
    * The function raises ``ValueError`` if the formula does not look
      like a perovskite or if the required elements cannot be identified.
    """
    comp = Composition(composition)
    # Identify X as oxygen if present, otherwise the element with the
    # highest count (heuristic for the anion).
    if "O" in comp:
        x_elem = Element("O")
    else:
        # Heuristic – pick the element with the smallest fraction as X.
        # This is only a fallback; the real dataset should contain O.
        x_elem = min(comp.elements, key=lambda e: comp.get_atomic_fraction(e))

    # Remove X from the set of elements to obtain A and B.
    remaining = [e for e in comp.elements if e != x_elem]
    if len(remaining) != 2:
        raise ValueError(
            f"Unable to infer A/B sites from composition '{composition}'."
        )
    a_elem, b_elem = sorted(remaining, key=lambda e: e.symbol)
    return a_elem, b_elem, x_elem


def _build_feature_row(row: pd.Series) -> dict:
    """
    Build a dictionary with the twelve descriptor columns for a single
    raw data row. Returns ``None`` if any descriptor cannot be obtained.
    """
    try:
        a_elem, b_elem, x_elem = _parse_perovskite(row["composition"])
    except Exception as exc:
        log.debug(f"Composition parsing failed for '{row['composition']}': {exc}")
        return None

    descriptors = {}
    for site, elem in zip(SITES, [a_elem, b_elem, x_elem]):
        radius, en, ox, val = _site_descriptors(elem)
        descriptors[f"{site}_atomic_radius"] = radius
        descriptors[f"{site}_electronegativity"] = en
        descriptors[f"{site}_oxidation_state"] = ox
        descriptors[f"{site}_valence_electrons"] = val

    # Add the target and composition columns.
    descriptors["formation_energy"] = row["formation_energy"]
    descriptors["composition"] = row["composition"]
    return descriptors


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def compute_features(input_csv: Path, output_csv: Path) -> None:
    """
    Reads ``input_csv`` (the raw defect CSV), computes the twelve
    compositional descriptors, drops rows with any missing descriptor,
    adds short radius columns (``*_radius``), writes the resulting
    feature matrix to ``output_csv``, and finally runs the descriptor‑gap
    checker which will raise if gaps remain.
    """
    log.info(f"Reading raw data from {input_csv}")
    raw_df = pd.read_csv(input_csv)

    if "composition" not in raw_df.columns or "formation_energy" not in raw_df.columns:
        raise ValueError(
            "Raw CSV must contain 'composition' and 'formation_energy' columns."
        )

    feature_dicts: List[dict] = []
    for _, row in raw_df.iterrows():
        feature_row = _build_feature_row(row)
        if feature_row is not None:
            feature_dicts.append(feature_row)

    if not feature_dicts:
        raise RuntimeError("No valid rows after descriptor computation.")

    features_df = pd.DataFrame(feature_dicts)

    # Drop rows with any missing descriptor values.
    descriptor_cols = [
        f"{site}_{desc}"
        for site in SITES
        for desc in DESCRIPTOR_NAMES
    ]
    before_drop = len(features_df)
    features_df = features_df.dropna(subset=descriptor_cols)
    dropped = before_drop - len(features_df)
    log.info(f"Dropped {dropped} rows with undefined descriptors (oxidation state, etc.).")
    featurize_log_path = paths.data("processed", "featurize.log")
    featurize_log_path.parent.mkdir(parents=True, exist_ok=True)
    with featurize_log_path.open("w", encoding="utf-8") as f:
        f.write(f"Dropped rows with missing descriptors: {dropped}\\n")

    # Add short radius columns (e.g. ``A_radius``) as copies of the long names.
    for site in SITES:
        long_name = f"{site}_atomic_radius"
        short_name = f"{site}_radius"
        features_df[short_name] = features_df[long_name]

    # Write the feature matrix.
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_csv, index=False)
    log.info(f"Feature matrix written to {output_csv}")

    # Run the descriptor‑gap checker – it will raise if any gaps remain.
    check_descriptor_gaps(features_path=output_csv)


def main() -> None:
    """
    CLI wrapper used by ``python -m src.featurize``.
    Expected positional arguments:
        1. Path to the raw CSV (input)
        2. Path to the output features CSV (output)
    """
    parser = argparse.ArgumentParser(
        description="Compute compositional descriptors for perovskite defect data."
    )
    parser.add_argument("input_csv", type=str, help="Path to raw defect CSV.")
    parser.add_argument("output_csv", type=str, help="Path for the engineered features CSV.")
    args = parser.parse_args()

    compute_features(Path(args.input_csv), Path(args.output_csv))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)
