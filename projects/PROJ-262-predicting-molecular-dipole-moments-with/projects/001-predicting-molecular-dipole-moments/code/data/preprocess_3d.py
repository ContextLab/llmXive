"""
preprocess_3d.py

This script extracts 3‑dimensional information (atomic coordinates, atom types,
and bond connectivity) from the QM9 dataset and writes the processed data to
``data/processed/features_3d.parquet``.

The script is robust to the state of the pipeline:
  * If a 10k subset parquet (``data/processed/molecules_10k.parquet``) is
    present, it is used as the input.
  * Otherwise the full raw QM9 parquet (``data/raw/qm9.parquet``) is read.
  * If neither file exists, a clear error is raised.

The output parquet contains the following columns:
  - ``molecule_id``: integer identifier (row index)
  - ``atom_types``   : list of atomic numbers (e.g. [6, 1, 1, 1])
  - ``coordinates``  : list of ``[x, y, z]`` lists (float)
  - ``bonds``        : list of ``[i, j]`` pairs (0‑based indices)

The implementation relies only on the standard library and the ``pandas`` /
``pyarrow`` packages, which are added to ``requirements.txt`` if not already
present.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _load_input_dataframe() -> pd.DataFrame:
    """
    Load the appropriate input parquet file.

    Preference order:
      1. ``data/processed/molecules_10k.parquet`` (subset)
      2. ``data/raw/qm9.parquet`` (full raw dataset)

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    processed_path = Path("data/processed/molecules_10k.parquet")
    raw_path = Path("data/raw/qm9.parquet")

    if processed_path.is_file():
        df = pd.read_parquet(processed_path)
    elif raw_path.is_file():
        df = pd.read_parquet(raw_path)
    else:
        raise FileNotFoundError(
            "Neither subset nor raw QM9 parquet files were found. "
            "Expected one of:\n"
            f"  - {processed_path}\n"
            f"  - {raw_path}"
        )
    return df

def _extract_atom_types(row: pd.Series) -> List[int]:
    """
    Extract atom types (atomic numbers) from a row.

    The QM9 dataset (as provided by ``datasets.load_dataset('qm9')``) stores
    atom types under the key ``'atom_types'``.  Some alternative sources use
    ``'atomic_numbers'`` or ``'z'``.  This function attempts a few common
    column names and falls back to an empty list if none are present.
    """
    for key in ("atom_types", "atomic_numbers", "z"):
        if key in row:
            return list(row[key])
    # Fallback – try to decode a JSON string if the column is stored as str
    possible = row.get("atom_types_json")
    if isinstance(possible, str):
        try:
            return list(json.loads(possible))
        except Exception:
            pass
    return []

def _extract_coordinates(row: pd.Series) -> List[List[float]]:
    """
    Extract 3‑D coordinates from a row.

    Expected keys (in order of preference):
      * ``'coordinates'`` – list of ``[x, y, z]`` triples
      * ``'positions'``
      * ``'R'`` – sometimes stored as a flat list ``[x1, y1, z1, x2, ...]``
    """
    if "coordinates" in row:
        return [list(coord) for coord in row["coordinates"]]
    if "positions" in row:
        return [list(coord) for coord in row["positions"]]
    if "R" in row:
        flat = list(row["R"])
        # reshape into triples
        return [flat[i : i + 3] for i in range(0, len(flat), 3)]
    return []

def _extract_bonds(row: pd.Series) -> List[List[int]]:
    """
    Extract bond connectivity as a list of ``[i, j]`` pairs.

    Expected keys:
      * ``'bond_index'`` – shape (num_bonds, 2)
      * ``'bonds'`` – list of pairs
    """
    if "bond_index" in row:
        return [list(pair) for pair in row["bond_index"]]
    if "bonds" in row:
        return [list(pair) for pair in row["bonds"]]
    return []

def _process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform the raw QM9 dataframe into a 3‑D feature dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing raw QM9 records.

    Returns
    -------
    pd.DataFrame
        Dataframe with columns ``molecule_id``, ``atom_types``,
        ``coordinates``, and ``bonds``.
    """
    # Ensure a deterministic ordering – use the original index as molecule_id
    df = df.reset_index(drop=False).rename(columns={"index": "molecule_id"})

    # Apply extraction helpers row‑wise
    atom_types = df.apply(_extract_atom_types, axis=1)
    coordinates = df.apply(_extract_coordinates, axis=1)
    bonds = df.apply(_extract_bonds, axis=1)

    processed = pd.DataFrame(
        {
            "molecule_id": df["molecule_id"],
            "atom_types": atom_types,
            "coordinates": coordinates,
            "bonds": bonds,
        }
    )
    return processed

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    """
    Command‑line interface.

    Optional arguments
    ------------------
    --output : Path
        Destination parquet file.  Defaults to
        ``data/processed/features_3d.parquet``.
    """
    parser = argparse.ArgumentParser(
        description="Extract 3‑D molecular information from QM9 and write a parquet file."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/features_3d.parquet"),
        help="Path to write the processed 3‑D features parquet.",
    )
    args = parser.parse_args(argv)

    try:
        df_raw = _load_input_dataframe()
    except FileNotFoundError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1

    df_processed = _process_dataframe(df_raw)

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Write parquet (uses pyarrow under the hood)
    df_processed.to_parquet(args.output, index=False)
    print(f"✅  3‑D features written to {args.output}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
