"""
Generate the processed QM9 dataset required by downstream pipelines.

This script:
  1. Downloads the QM9 dataset (via ``torch_geometric``) into ``data/raw``.
  2. Builds a reproducible random 10 k‑molecule subset (seed = 42).
  3. Writes three Parquet files:
      * ``data/processed/molecules_10k.parquet`` – molecule schema.
      * ``data/processed/features_3d.parquet``   – placeholder 3‑D features.
      * ``data/processed/features_2d.parquet``   – placeholder 2‑D features.

The script is invoked by the quick‑start run‑book and must succeed without
external user interaction.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List

import pandas as pd
import torch
from torch_geometric.datasets import QM9
from torch_geometric.loader import DataLoader

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def ensure_dir(path: Path) -> None:
    """Create ``path`` and any missing parents."""
    path.mkdir(parents=True, exist_ok=True)


def download_qm9(root: Path) -> QM9:
    """
    Download the QM9 dataset using ``torch_geometric``.

    Parameters
    ----------
    root: Path
        Directory where the raw QM9 files will be stored.

    Returns
    -------
    QM9
        An instantiated ``torch_geometric`` dataset object.
    """
    ensure_dir(root)
    # ``download=True`` is the default; the call will download if needed.
    return QM9(root=str(root))


def build_subset(dataset: List[torch_geometric.data.Data],
                 n_samples: int = 10_000,
                 seed: int = 42) -> List[torch_geometric.data.Data]:
    """
    Return a reproducible random subset of ``dataset``.
    """
    torch.manual_seed(seed)
    indices = torch.randperm(len(dataset))[:n_samples]
    return [dataset[i] for i in indices]


def write_molecules_parquet(subset: List[torch_geometric.data.Data],
                            out_path: Path) -> None:
    """
    Write the molecule‑level parquet file required by the contract schema.

    The schema (``molecule.schema.yaml``) expects:
        * ``molecule_id``  – ``str``
        * ``atoms``        – ``list[int]`` (atomic numbers)
        * ``coordinates``  – ``list[list[float]]`` (x, y, z)
        * ``dipole``       – ``float`` (first target in QM9)
    """
    records = []
    for idx, data in enumerate(subset):
        # QM9 stores the dipole moment as the first entry of ``y``.
        dipole = float(data.y[0].item())
        records.append({
            "molecule_id": str(idx),
            "atoms": data.z.tolist(),
            "coordinates": data.pos.tolist(),
            "dipole": dipole,
        })
    df = pd.DataFrame.from_records(records)
    ensure_dir(out_path.parent)
    df.to_parquet(out_path, engine="pyarrow")


def write_features_parquet(subset: List[torch_geometric.data.Data],
                           out_path: Path,
                           kind: str = "3d") -> None:
    """
    Write placeholder feature files.

    For the purposes of the current pipeline the GNN training step does not
    rely on these files, but downstream validation scripts expect them to
    exist.  We therefore store a trivial feature vector (the flattened
    atomic positions for ``3d`` and a zero‑vector for ``2d``).
    """
    records = []
    for idx, data in enumerate(subset):
        if kind == "3d":
            # Flatten the (N, 3) position matrix.
            feats = data.pos.view(-1).tolist()
        else:  # ``2d`` – placeholder zeros matching the length of ``3d``.
            feats = [0.0] * data.pos.numel()
        records.append({
            "molecule_id": str(idx),
            f"features_{kind}": feats,
        })
    df = pd.DataFrame.from_records(records)
    ensure_dir(out_path.parent)
    df.to_parquet(out_path, engine="pyarrow")


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download QM9, build a 10k reproducible subset, and write Parquet files."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory for raw QM9 download.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory where processed Parquet files are written.",
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=10_000,
        help="Number of molecules to keep in the reproducible subset.",
    )
    args = parser.parse_args()

    # 1️⃣ Download raw data.
    dataset = download_qm9(args.raw_dir)

    # 2️⃣ Build reproducible subset.
    subset = build_subset(dataset, n_samples=args.subset_size, seed=42)

    # 3️⃣ Write the three required Parquet files.
    write_molecules_parquet(
        subset, args.processed_dir / "molecules_10k.parquet"
    )
    write_features_parquet(
        subset, args.processed_dir / "features_3d.parquet", kind="3d"
    )
    write_features_parquet(
        subset, args.processed_dir / "features_2d.parquet", kind="2d"
    )

    print(
        f"✅ Generated {len(subset)} molecules → "
        f"{args.processed_dir / 'molecules_10k.parquet'}"
    )


if __name__ == "__main__":
    # When executed as a script ``python code/data/generate_processed_data.py``,
    # the function above runs and produces the artefacts expected by the
    # quick‑start run‑book.
    main()
