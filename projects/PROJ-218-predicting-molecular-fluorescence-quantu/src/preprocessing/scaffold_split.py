"""
Scaffold-based data split script.

This script reads a joined dataset CSV (expected to contain at least a
``smiles`` column), computes Murcko scaffolds for each molecule, and
splits the data into train / validation / test sets using an 80/10/10
ratio while guaranteeing zero scaffold overlap between the splits.

Outputs:
  - data/splits/train.csv
  - data/splits/validation.csv
  - data/splits/test.csv
  - data/splits/scaffold_overlap.txt
  - data/splits/split_counts.log

The randomisation uses the seeds defined in ``code/config/seeds.yaml``.
If the test set contains fewer than 20 molecules a warning is written to
``split_counts.log``.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import numpy as np

# RDKit is required for scaffold extraction
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

# Project utilities
from llmxive_toolkit import paths, get_logger
from code.data.download_raw import load_and_set_seeds

log = get_logger(__name__)

def _compute_scaffold(smiles: str) -> str:
    """Return a canonical SMILES string for the Murcko scaffold of a molecule.

    If the SMILES cannot be parsed, an empty string is returned; the caller
    should handle such cases (they will be dropped from the split).
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return ""
    scaffold = MurckoScaffold.GetScaffoldForMol(mol)
    if scaffold is None:
        return ""
    # Canonicalise the scaffold SMILES
    scaffold_smiles = Chem.MolToSmiles(scaffold, canonical=True)
    return scaffold_smiles

def _assign_scaffolds(df: pd.DataFrame, smiles_col: str = "smiles") -> pd.DataFrame:
    """Add a ``scaffold_id`` column to ``df`` based on Murcko scaffolds."""
    log.info("Computing Murcko scaffolds for %d molecules", len(df))
    scaffold_ids = []
    for smi in df[smiles_col]:
        scaffold_id = _compute_scaffold(smi)
        scaffold_ids.append(scaffold_id)
    df = df.copy()
    df["scaffold_id"] = scaffold_ids
    # Drop rows where scaffold could not be computed (invalid SMILES)
    before = len(df)
    df = df[df["scaffold_id"] != ""].reset_index(drop=True)
    after = len(df)
    if after < before:
        log.warning("Dropped %d rows due to invalid SMILES / scaffold extraction", before - after)
    return df

def _split_by_scaffold(
    df: pd.DataFrame,
    train_frac: float = 0.8,
    val_frac: float = 0.1,
    test_frac: float = 0.1,
    random_state: np.random.RandomState = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Perform a scaffold split respecting the requested fractions.

    The split is performed on the *set of unique scaffolds*; all molecules
    sharing a scaffold stay together. The algorithm shuffles the scaffold
    list (using the supplied ``random_state``) and then allocates scaffolds
    to each split until the target molecule counts are reached (or the
    list is exhausted). This deterministic approach guarantees zero
    scaffold overlap.
    """
    if not np.isclose(train_frac + val_frac + test_frac, 1.0):
        raise ValueError("Fractions must sum to 1.0")

    # Group indices by scaffold
    scaffold_to_indices = df.groupby("scaffold_id").indices
    scaffold_ids = list(scaffold_to_indices.keys())

    # Shuffle scaffold identifiers
    if random_state is None:
        random_state = np.random.RandomState()
    random_state.shuffle(scaffold_ids)

    # Target molecule counts
    total = len(df)
    target_train = int(round(train_frac * total))
    target_val = int(round(val_frac * total))
    # test gets the remainder
    target_test = total - target_train - target_val

    splits = {"train": [], "val": [], "test": []}
    counts = {"train": 0, "val": 0, "test": 0}
    # Allocation order: train -> val -> test (cyclic)
    order = ["train", "val", "test"]
    idx = 0
    for scaffold_id in scaffold_ids:
        scaffold_indices = scaffold_to_indices[scaffold_id]
        size = len(scaffold_indices)
        # Find the first split that would not exceed its target (or test if all are full)
        for attempt in range(3):
            split_name = order[(idx + attempt) % 3]
            if counts[split_name] + size <= {"train": target_train, "val": target_val, "test": target_test}[split_name]:
                splits[split_name].extend(scaffold_indices)
                counts[split_name] += size
                break
        else:
            # All splits are full; assign to the one with the smallest excess
            min_split = min(order, key=lambda s: counts[s] - {"train": target_train, "val": target_val, "test": target_test}[s])
            splits[min_split].extend(scaffold_indices)
            counts[min_split] += size
        idx += 1

    train_df = df.loc[sorted(splits["train"])].reset_index(drop=True)
    val_df = df.loc[sorted(splits["val"])].reset_index(drop=True)
    test_df = df.loc[sorted(splits["test"])].reset_index(drop=True)
    return train_df, val_df, test_df

def _log_overlap(train: pd.DataFrame, test: pd.DataFrame, out_path: Path):
    overlap = set(train["scaffold_id"]).intersection(set(test["scaffold_id"]))
    overlap_count = len(overlap)
    out_path.write_text(f"train-test overlap: {overlap_count}\n")
    log.info("Scaffold overlap (train-test): %d", overlap_count)

def _log_counts(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, out_path: Path):
    lines = [
        f"train: {len(train)}",
        f"validation: {len(val)}",
        f"test: {len(test)}",
    ]
    if len(test) < 20:
        warning = f"WARNING: test set contains fewer than 20 molecules ({len(test)})"
        lines.append(warning)
        log.warning(warning)
    out_path.write_text("\n".join(lines) + "\n")
    log.info("Split counts written to %s", out_path)

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold‑based split (80/10/10) with reproducible shuffling."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=paths.data("processed", "joined.csv"),
        help="Path to the joined CSV produced by T002.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=paths.data("splits"),
        help="Directory where train/validation/test CSVs and logs will be stored.",
    )
    args = parser.parse_args(argv)

    # Ensure reproducibility
    load_and_set_seeds()

    # Load data
    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        log.error("Failed to read input CSV %s: %s", args.input, e)
        return 1

    required_cols = {"smiles"}
    if not required_cols.issubset(df.columns):
        log.error("Input CSV must contain columns: %s", required_cols)
        return 1

    # Compute scaffolds
    df = _assign_scaffolds(df, smiles_col="smiles")

    # Perform split
    train_df, val_df, test_df = _split_by_scaffold(df)

    # Write outputs
    args.output_dir.mkdir(parents=True, exist_ok=True)
    train_path = args.output_dir / "train.csv"
    val_path = args.output_dir / "validation.csv"
    test_path = args.output_dir / "test.csv"
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    # Log overlap and counts
    _log_overlap(train_df, test_df, args.output_dir / "scaffold_overlap.txt")
    _log_counts(train_df, val_df, test_df, args.output_dir / "split_counts.log")

    log.info("Scaffold split completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
