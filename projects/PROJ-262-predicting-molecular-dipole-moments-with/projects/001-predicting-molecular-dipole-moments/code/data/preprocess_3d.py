"""preprocess_3d.py
-----------------
Extract 3‑D geometric information (atom types, Cartesian coordinates,
and bond connectivity) from the QM9 dataset and store a reproducible
10 000‑molecule subset as a Parquet file.

The script is deliberately self‑contained so that it can be run
independently of the earlier `download_qm9.py` and `create_subset.py`
steps – this guarantees that the end‑to‑end quick‑start run‑book
succeeds even when those scripts fail.

Output
------
The script writes a Parquet file to:
    data/processed/molecules_10k.parquet

The file contains the following columns:
  * ``molecule_id`` – integer identifier (0‑based)
  * ``atom_numbers`` – list of atomic numbers (int)
  * ``positions``    – list of ``[x, y, z]`` coordinates (float)
  * ``bond_index``   – list of ``[i, j]`` pairs representing bonds

Dependencies
------------
* ``datasets`` – HuggingFace datasets library (provides the QM9 dataset)
* ``pandas``   – for DataFrame handling and Parquet I/O
* ``tqdm``     – progress bar
* ``pyarrow``  – Parquet engine (installed as a pandas extra)
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from datasets import load_dataset
from tqdm import tqdm


def _ensure_output_dir(output_path: Path) -> None:
    """Create parent directories for the output file if they do not exist."""
    output_path.parent.mkdir(parents=True, exist_ok=True)


def _sample_subset(
    dataset, n_samples: int, seed: int
) -> List[Tuple[int, dict]]:
    """Return ``n_samples`` random entries from ``dataset`` with reproducibility.

    Parameters
    ----------
    dataset
        The HuggingFace dataset object.
    n_samples
        Number of molecules to keep.
    seed
        Random seed for reproducibility.

    Returns
    -------
    List of ``(index, entry)`` tuples.
    """
    random.seed(seed)
    total = len(dataset)
    if n_samples > total:
        raise ValueError(
            f"Requested {n_samples} samples but dataset only contains {total} entries."
        )
    indices = random.sample(range(total), n_samples)
    return [(i, dataset[i]) for i in indices]


def _extract_atom_numbers(entry: dict) -> List[int]:
    """Extract atomic numbers from a QM9 entry.

    The QM9 dataset may expose the information under different keys
    depending on the source version.  We try a few common alternatives.
    """
    for key in ("z", "atom_type", "atomic_numbers"):
        if key in entry:
            return list(entry[key])
    raise KeyError("Atomic numbers not found in QM9 entry.")


def _extract_positions(entry: dict) -> List[List[float]]:
    """Extract Cartesian coordinates from a QM9 entry.

    The coordinates are typically stored as a ``(N, 3)`` array under
    ``positions`` or ``R``.  The function returns a plain Python list.
    """
    for key in ("positions", "R", "coordinates"):
        if key in entry:
            # ``entry[key]`` may be a list of lists or a NumPy array.
            return [list(map(float, pos)) for pos in entry[key]]
    raise KeyError("3‑D positions not found in QM9 entry.")


def _extract_bond_index(entry: dict) -> List[List[int]]:
    """Extract bond connectivity.

    QM9 does not store explicit bonds; however, many versions provide an
    ``edge_index`` tensor (shape ``[2, n_bonds]``).  If unavailable we
    construct a simple distance‑based adjacency with a 1.6 Å cutoff – a
    common heuristic for covalent bonds in organic molecules.
    """
    if "edge_index" in entry:
        # edge_index shape: [2, n_bonds]
        edges = entry["edge_index"]
        # Convert to list of [i, j] pairs
        return [[int(i), int(j)] for i, j in zip(edges[0], edges[1])]

    # Fallback: distance‑based adjacency
    positions = _extract_positions(entry)
    n_atoms = len(positions)
    bonds: List[List[int]] = []
    cutoff = 1.6  # Å
    for i in range(n_atoms):
        xi, yi, zi = positions[i]
        for j in range(i + 1, n_atoms):
            xj, yj, zj = positions[j]
            dist = ((xi - xj) ** 2 + (yi - yj) ** 2 + (zi - zj) ** 2) ** 0.5
            if dist <= cutoff:
                bonds.append([i, j])
    return bonds


def _process_entry(idx: int, entry: dict) -> dict:
    """Convert a raw QM9 entry into the schema used for downstream pipelines."""
    return {
        "molecule_id": idx,
        "atom_numbers": _extract_atom_numbers(entry),
        "positions": _extract_positions(entry),
        "bond_index": _extract_bond_index(entry),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract 3‑D geometry, atom types, and bonds from QM9."
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=10_000,
        help="Number of molecules to include in the subset (default: 10 000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling (default: 42).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to the output Parquet file. If omitted, defaults to "
        "data/processed/molecules_10k.parquet relative to the project root.",
    )
    args = parser.parse_args()

    # Resolve output location
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        # ``preprocess_3d.py`` lives in
        #   projects/001-predicting-molecular-dipole-moments/code/data/
        # The project root is two directories up from this file.
        project_root = Path(__file__).resolve().parents[2]
        output_path = project_root / "data" / "processed" / "molecules_10k.parquet"

    _ensure_output_dir(output_path)

    # Load QM9 via HuggingFace – this will download the dataset once and cache it.
    print("Downloading/loading QM9 dataset ...")
    qm9 = load_dataset("qm9", split="train")  # type: ignore[arg-type]

    # Sample a reproducible subset
    subset = _sample_subset(qm9, args.samples, args.seed)

    # Process entries with a progress bar
    rows = []
    print(f"Processing {len(subset)} molecules ...")
    for idx, entry in tqdm(subset, desc="Extracting 3D info"):
        rows.append(_process_entry(idx, entry))

    df = pd.DataFrame(rows)

    # Write to Parquet (pyarrow engine)
    df.to_parquet(output_path, engine="pyarrow", index=False)
    print(f"✅  Finished – {len(df)} records written to {output_path}")


if __name__ == "__main__":
    main()
