"""
src/data/featurize.py
---------------------

Implements compositional featurization for perovskite defect data.
The public API consists of:
  * _add_short_radius_columns – copies long radius column names to the short ones required by the schema.
  * compute_features – reads the raw CSV, computes the twelve compositional descriptors,
    drops rows with undefined oxidation states, writes logs, adds short radius columns,
    checks for descriptor gaps and writes the final feature matrix.
  * main – CLI entry point used by ``python -m src.featurize``.
"""

import argparse
import sys
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from pymatgen.core import Composition, Element
from llmxive_toolkit import get_logger, paths

from src.utils.check_descriptor_gaps import check_descriptor_gaps

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper: add short radius columns (A_radius, B_radius, X_radius)
# ----------------------------------------------------------------------
def _add_short_radius_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    The original implementation stored atomic radii under the name
    ``*_atomic_radius``.  The feature‑matrix schema (see
    ``contracts/features.schema.yaml``) requires the shorter column names
    ``*_radius``.  To preserve compatibility with downstream utilities that
    still reference the long names, we keep both columns – the short names
    are copies of the long ones.
    """
    for site in ["A", "B", "X"]:
        long_name = f"{site}_atomic_radius"
        short_name = f"{site}_radius"
        if long_name in df.columns:
            df[short_name] = df[long_name]
    return df

# ----------------------------------------------------------------------
# Core feature computation
# ----------------------------------------------------------------------
def compute_features(input_csv: Path, output_csv: Path) -> None:
    """
    Read the raw defect CSV, compute the twelve compositional descriptors,
    drop rows with any undefined descriptor (including oxidation state),
    add short radius columns, write the final feature matrix, and finally
    run the descriptor‑gap checker which will raise if gaps remain.

    Parameters
    ----------
    input_csv : Path
        Path to the raw CSV produced by ``src.data.download``.
    output_csv : Path
        Destination path for the engineered feature matrix.
    """
    # ------------------------------------------------------------------
    # 1. Load raw data
    # ------------------------------------------------------------------
    try:
        raw_df = pd.read_csv(input_csv)
    except Exception as exc:
        log.error(f"Failed to read raw CSV at {input_csv}: {exc}")
        raise

    required_raw_cols = {"composition", "formation_energy"}
    missing_raw = required_raw_cols - set(raw_df.columns)
    if missing_raw:
        raise RuntimeError(f"Raw CSV missing required columns: {missing_raw}")

    # ------------------------------------------------------------------
    # 2. Compute descriptors for each row
    # ------------------------------------------------------------------
    feature_rows: List[dict] = []
    rows_dropped_missing_oxi = 0

    for _, row in raw_df.iterrows():
        comp_str: str = row["composition"]
        formation_energy = row["formation_energy"]

        # Parse composition with pymatgen
        try:
            comp = Composition(comp_str)
        except Exception:
            # Unable to parse composition – drop the row
            rows_dropped_missing_oxi += 1
            continue

        # Identify X (oxygen) if present, otherwise take the last element
        elements = list(comp.elements)
        if any(el.symbol == "O" for el in elements):
            x_elem = "O"
            cation_elements = [el for el in elements if el.symbol != "O"]
        else:
            # Fallback: treat the last element as X
            x_elem = elements[-1].symbol
            cation_elements = elements[:-1]

        if len(cation_elements) < 2:
            # Not enough cations to assign A and B – drop the row
            rows_dropped_missing_oxi += 1
            continue

        # Assign A and B (order is not critical for the current descriptor set)
        a_elem = cation_elements[0].symbol
        b_elem = cation_elements[1].symbol

        # ----------------------------------------------------------------
        # Oxidation state determination
        # ----------------------------------------------------------------
        try:
            oxi_guess_list = comp.oxi_state_guesses()
            oxi_dict = oxi_guess_list[0] if oxi_guess_list else {}
        except Exception:
            oxi_dict = {}

        def get_oxi(sym: str):
            return oxi_dict.get(sym, np.nan)

        # ----------------------------------------------------------------
        # Gather element objects
        # ----------------------------------------------------------------
        try:
            A = Element(a_elem)
            B = Element(b_elem)
            X = Element(x_elem)
        except Exception:
            # If any element is unknown to pymatgen, drop the row
            rows_dropped_missing_oxi += 1
            continue

        # ----------------------------------------------------------------
        # Build descriptor dictionary
        # ----------------------------------------------------------------
        descriptor_dict = {
            "composition": comp_str,
            "formation_energy": formation_energy,
            # Atomic radii (long names)
            "A_atomic_radius": A.atomic_radius,
            "B_atomic_radius": B.atomic_radius,
            "X_atomic_radius": X.atomic_radius,
            # Electronegativity (Pauling)
            "A_electronegativity": A.electronegativity,
            "B_electronegativity": B.electronegativity,
            "X_electronegativity": X.electronegativity,
            # Oxidation states
            "A_oxidation_state": get_oxi(a_elem),
            "B_oxidation_state": get_oxi(b_elem),
            "X_oxidation_state": get_oxi(x_elem),
            # Valence electron count
            "A_valence_electrons": A.valence_electrons,
            "B_valence_electrons": B.valence_electrons,
            "X_valence_electrons": X.valence_electrons,
        }

        feature_rows.append(descriptor_dict)

    # ------------------------------------------------------------------
    # 3. Create DataFrame and drop rows with any missing descriptor
    # ------------------------------------------------------------------
    features_df = pd.DataFrame(feature_rows)

    # Identify descriptor columns (excluding target & composition)
    descriptor_cols = [
        col
        for col in features_df.columns
        if col not in {"composition", "formation_energy"}
    ]

    before_drop = len(features_df)
    features_df = features_df.dropna(subset=descriptor_cols)
    rows_dropped_missing_desc = before_drop - len(features_df)

    total_dropped = rows_dropped_missing_oxi + rows_dropped_missing_desc

    # ------------------------------------------------------------------
    # 4. Write featurize.log
    # ------------------------------------------------------------------
    featurize_log_path = paths.data("processed", "featurize.log")
    featurize_log_path.parent.mkdir(parents=True, exist_ok=True)
    with featurize_log_path.open("w", encoding="utf-8") as f:
        f.write(f"Dropped {total_dropped} rows due to missing descriptors or oxidation states.\\n")

    # ------------------------------------------------------------------
    # 5. Add short radius columns required by the schema
    # ------------------------------------------------------------------
    features_df = _add_short_radius_columns(features_df)

    # ------------------------------------------------------------------
    # 6. Write the final feature matrix
    # ------------------------------------------------------------------
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_csv, index=False)

    # ------------------------------------------------------------------
    # 7. Verify that no descriptor gaps remain
    # ------------------------------------------------------------------
    # This will write ``descriptor_gaps.log`` and raise RuntimeError if gaps exist.
    check_descriptor_gaps(features_path=output_csv)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI wrapper used by ``python -m src.featurize``.

    Expected positional arguments:
        1. Path to the raw CSV (input)
        2. Path to the output features CSV
    """
    parser = argparse.ArgumentParser(description="Compute perovskite compositional features")
    parser.add_argument("input_csv", type=Path, help="Path to raw defect CSV")
    parser.add_argument("output_csv", type=Path, help="Path where features CSV will be written")
    args = parser.parse_args()

    try:
        compute_features(args.input_csv, args.output_csv)
    except Exception as exc:
        log.error(f"Feature computation failed: {exc}")
        sys.exit(1)
