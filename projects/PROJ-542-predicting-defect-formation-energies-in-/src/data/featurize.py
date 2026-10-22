"""
src/data/featurize.py
---------------------

Implements the feature engineering step for the perovskite defect formation
energy pipeline.  The module reads a raw CSV containing at least the columns
``composition`` (e.g. ``BaTiO3``) and ``formation_energy``.  For each composition
it extracts the A, B, and X elements, computes four compositional descriptors
(atomic radius, electronegativity, oxidation state, valence electron count)
using ``pymatgen`` and writes a feature matrix that conforms to
``contracts/features.schema.yaml``.

The implementation follows the requirements of task **T003**:

* 12 descriptor columns (4 descriptors × 3 sites) are produced.
* Rows where any descriptor cannot be determined are dropped; the count
  of dropped rows is written to ``data/processed/featurize.log``.
* After dropping, if any descriptor column still contains missing values,
  a ``RuntimeError`` is raised and details are written to
  ``data/processed/descriptor_gaps.log``.
* The output CSV does **not** contain the ``composition`` column – this is
  required by the JSON‑Schema contract.
* A SHA‑256 checksum of the output CSV is written to
  ``data/checksums/features.sha256`` via the utility in ``src.utils.checksum``.
* All paths are created using the ``llmxive_toolkit.paths`` helpers, ensuring
  the correct project‑relative locations.
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import pandas as pd
from pymatgen.core.periodic_table import Element

from llmxive_toolkit import get_logger, paths
from src.utils.checksum import write_checksum

log = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def _site_descriptors(elem: Element) -> Tuple[Optional[float], Optional[float], Optional[int], Optional[int]]:
    """
    Return the four required compositional descriptors for a single element.

    Parameters
    ----------
    elem : Element
        pymatgen Element instance.

    Returns
    -------
    Tuple[Optional[float], Optional[float], Optional[int], Optional[int]]
        (covalent radius in Å, Pauling electronegativity,
         most common oxidation state, valence electron count).
         Any of the values may be ``None`` if the information is unavailable.
    """
    # Covalent radius (Å). ``elem.covalent_radius`` may be ``None``.
    radius = elem.covalent_radius

    # Pauling electronegativity.
    electronegativity = elem.electronegativity

    # Most common oxidation state – the first entry in the list, if present.
    oxidation_state: Optional[int] = None
    if elem.oxidation_states:
        # ``oxidation_states`` is a list of ints sorted by frequency.
        oxidation_state = elem.oxidation_states[0]

    # Valence electron count – ``elem.full_electronic_structure`` provides
    # the configuration; ``elem.valence`` is a convenient property.
    valence_electrons: Optional[int] = getattr(elem, "valence", None)

    return radius, electronegativity, oxidation_state, valence_electrons

def _parse_perovskite(composition: str) -> Tuple[Element, Element, Element]:
    """
    Very simple parser for ABX₃ formulas that contain oxygen as the X site.

    The function extracts the three distinct element symbols, orders the
    non‑oxygen symbols alphabetically to obtain deterministic A / B
    assignment, and returns the corresponding ``Element`` objects.

    Parameters
    ----------
    composition : str
        Chemical formula, e.g. ``BaTiO3``.

    Returns
    -------
    Tuple[Element, Element, Element]
        (A, B, X) element objects.

    Raises
    ------
    ValueError
        If the formula does not contain exactly three distinct elements
        (including oxygen) or if any symbol cannot be resolved by pymatgen.
    """
    # Remove whitespace and split into element symbols using pymatgen's
    # ``Composition`` parser for robustness.
    from pymatgen.core import Composition  # Imported locally to avoid circular import.

    comp = Composition(composition)
    symbols = sorted(comp.elements, key=lambda e: e.symbol)
    # Identify oxygen element.
    ox = None
    others: List[Element] = []
    for el in symbols:
        if el.symbol == "O":
            ox = el
        else:
            others.append(el)

    if ox is None:
        raise ValueError(f"Oxygen not found in composition '{composition}'")
    if len(others) != 2:
        raise ValueError(f"Expected exactly two non‑oxygen elements in '{composition}', got {len(others)}")

    # Deterministic ordering: alphabetical.
    A, B = sorted(others, key=lambda e: e.symbol)
    X = ox
    return A, B, X

def _build_feature_row(row: pd.Series) -> Optional[Dict[str, Any]]:
    """
    Build a dictionary containing the twelve descriptor columns for a single
    raw data row.  If any descriptor is ``None`` the row is considered invalid
    and ``None`` is returned so that the caller can drop it.

    Parameters
    ----------
    row : pd.Series
        A row from the raw CSV. Must contain a ``composition`` column.

    Returns
    -------
    dict | None
        Mapping from column name to descriptor value (including the target
        ``formation_energy``), or ``None`` if the row should be omitted.
    """
    try:
        A, B, X = _parse_perovskite(row["composition"])
    except Exception as e:
        log.warning(f"Failed to parse composition '{row.get('composition')}' – {e}")
        return None

    # Compute descriptors for each site.
    descriptors = {}
    for site, elem in zip(("A", "B", "X"), (A, B, X)):
        radius, en, ox_state, val_e = _site_descriptors(elem)
        if any(v is None for v in (radius, en, ox_state, val_e)):
            # Missing descriptor – drop this row.
            return None
        descriptors[f"{site}_atomic_radius"] = radius
        descriptors[f"{site}_electronegativity"] = en
        descriptors[f"{site}_oxidation_state"] = ox_state
        descriptors[f"{site}_valence_electrons"] = val_e

    # Include the target variable.
    descriptors["formation_energy"] = row["formation_energy"]
    return descriptors

# -------------------------------------------------------------------------
# Core implementation
# -------------------------------------------------------------------------

def compute_features(input_csv: Path, output_csv: Path) -> None:
    """
    Read the raw defect CSV, compute compositional descriptors, write the
    feature matrix, and generate auxiliary logs and checksum.

    Parameters
    ----------
    input_csv : Path
        Path to ``data/raw/materials_defects.csv`` (or a user‑provided CSV
        with the same schema).
    output_csv : Path
        Destination for ``data/processed/features.csv``.
    """
    input_path = Path(input_csv)
    output_path = Path(output_csv)

    if not input_path.is_file():
        raise FileNotFoundError(f"Raw dataset not found at {input_path}")

    # Ensure output directories exist.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_dir = paths.data("processed")
    log_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # Load raw data.
    # -----------------------------------------------------------------
    raw_df = pd.read_csv(input_path)

    required_raw_cols = {"composition", "formation_energy"}
    if not required_raw_cols.issubset(set(raw_df.columns)):
        missing = required_raw_cols - set(raw_df.columns)
        raise RuntimeError(f"Raw CSV is missing required columns: {missing}")

    # -----------------------------------------------------------------
    # Build feature rows.
    # -----------------------------------------------------------------
    feature_rows: List[Dict[str, Any]] = []
    dropped_count = 0

    for _, row in raw_df.iterrows():
        feature_dict = _build_feature_row(row)
        if feature_dict is None:
            dropped_count += 1
            continue
        feature_rows.append(feature_dict)

    # Write featurize.log
    featurize_log_path = paths.data("processed", "featurize.log")
    with featurize_log_path.open("w") as f_log:
        f_log.write(f"Dropped {dropped_count} rows due to missing descriptors or parsing errors.\n")

    # -----------------------------------------------------------------
    # Create DataFrame from collected rows.
    # -----------------------------------------------------------------
    if not feature_rows:
        raise RuntimeError("All rows were dropped – no features to write.")

    features_df = pd.DataFrame(feature_rows)

    # Verify that no descriptor column contains missing values.
    descriptor_cols = [col for col in features_df.columns if col != "formation_energy"]
    gaps = features_df[descriptor_cols].isnull().any()
    if gaps.any():
        # Write detailed gaps log.
        descriptor_gaps_path = paths.data("processed", "descriptor_gaps.log")
        with descriptor_gaps_path.open("w") as f_gap:
            f_gap.write("Descriptor gaps detected:\n")
            for col in descriptor_cols:
                if features_df[col].isnull().any():
                    rows_missing = features_df[features_df[col].isnull()].index.tolist()
                    f_gap.write(f"- Column {col} missing in rows {rows_missing}\n")
        raise RuntimeError("Descriptor gaps detected – see descriptor_gaps.log")

    # If we reach here, there are no gaps – write a success message.
    descriptor_gaps_path = paths.data("processed", "descriptor_gaps.log")
    with descriptor_gaps_path.open("w") as f_gap:
        f_gap.write("No descriptor gaps found.\n")

    # -----------------------------------------------------------------
    # Write the feature CSV (without the composition column).
    # -----------------------------------------------------------------
    # Ensure column order matches the schema (alphabetical order of columns
    # is acceptable because the schema does not enforce ordering).
    features_df.to_csv(output_path, index=False)

    # -----------------------------------------------------------------
    # Compute checksum for the features CSV.
    # -----------------------------------------------------------------
    checksum_dir = paths.checksums()
    checksum_dir.mkdir(parents=True, exist_ok=True)
    write_checksum(output_path, checksum_dir)

    log.info(f"Feature engineering completed: {len(features_df)} rows written to {output_path}")

# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------

def _parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute compositional descriptors for perovskite defect data."
    )
    parser.add_argument(
        "input_csv",
        type=str,
        help="Path to the raw CSV file (e.g., data/raw/materials_defects.csv).",
    )
    parser.add_argument(
        "output_csv",
        type=str,
        help="Path where the processed feature matrix will be written.",
    )
    return parser.parse_args()

def main() -> None:
    """
    CLI wrapper used by ``python -m src.data.featurize``.
    """
    args = _parse_cli_args()
    try:
        compute_features(Path(args.input_csv), Path(args.output_csv))
    except Exception as e:
        log.error(f"Featurization failed: {e}")
        # Re‑raise to ensure a non‑zero exit status for the CLI.
        raise

if __name__ == "__main__":
    main()