"""
Scaffold‑based splitting script.

This script reads the processed dataset (``data/processed/filtered.csv``),
computes Murcko scaffolds for each molecule, and generates **5 × 5**
scaffold splits (outer seeds 100‑104, inner seeds 200‑204).  For each
combination it writes three CSV files:

    data/splits/train_{i}_{j}.csv
    data/splits/val_{i}_{j}.csv
    data/splits/test_{i}_{j}.csv

where *i* ∈ {1..5} (outer fold) and *j* ∈ {1..5} (inner repeat).

The script enforces:
  • 80 % / 10 % / 10 % train‑val‑test split (within 1 % tolerance)
  • Zero scaffold overlap between train and test sets
  • Validation of each split against ``contracts/dataset.schema.yaml``
    using the lightweight validator from ``code/data/download.py``.

Usage (run from the repository root after ``cd code``):
    python data/split.py
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from jsonschema import Draft7Validator, ValidationError

from llmxive_toolkit import paths, get_logger

# Import the minimal validator used elsewhere in the project.
# The function validates the essential columns (smiles, refractive_index,
# molecular_weight, node_features, edge_features).
from data.download import validate_rows

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def murcko_scaffold(smiles: str) -> str:
    """
    Return the canonical SMILES of the Murcko scaffold for a molecule.
    If RDKit cannot generate a scaffold, an empty string is returned.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return ""
    scaffold = MurckoScaffold.GetScaffoldForMol(mol)
    if scaffold is None:
        return ""
    return Chem.MolToSmiles(scaffold, isomericSmiles=True)


def allocate_scaffolds(
    scaffold_to_indices: dict,
    total_len: int,
    ratios: tuple[float, float, float],
    rng: random.Random,
) -> tuple[list[int], list[int], list[int]]:
    """
    Allocate whole scaffolds to train/val/test respecting the target
    molecule counts as closely as possible.

    Returns three lists of row indices for train, val, and test.
    """
    target_train = int(ratios[0] * total_len)
    target_val = int(ratios[1] * total_len)
    # Ensure the three sets sum to the total number of rows.
    target_test = total_len - target_train - target_val

    # Shuffle scaffold list deterministically.
    scaffolds = list(scaffold_to_indices.keys())
    rng.shuffle(scaffolds)

    train_idx, val_idx, test_idx = [], [], []
    counts = [0, 0, 0]  # current molecule counts for train/val/test

    for scaf in scaffolds:
        indices = scaffold_to_indices[scaf]
        # Decide where to place this scaffold.
        # Prefer the split that is still furthest from its target.
        deficits = [
            target_train - counts[0],
            target_val - counts[1],
            target_test - counts[2],
        ]
        # Choose the split with the largest positive deficit.
        # If all deficits are <= 0, put into the split with the smallest overflow.
        if max(deficits) > 0:
            split = deficits.index(max(deficits))
        else:
            # All targets reached; assign to the split with the smallest current size.
            split = min(range(3), key=lambda i: counts[i])

        if split == 0:
            train_idx.extend(indices)
        elif split == 1:
            val_idx.extend(indices)
        else:
            test_idx.extend(indices)

        counts[split] += len(indices)

    return train_idx, val_idx, test_idx


def verify_split(
    train_scaffolds: set,
    test_scaffolds: set,
    train_len: int,
    val_len: int,
    test_len: int,
    total_len: int,
    ratios: tuple[float, float, float],
) -> None:
    """
    Perform the assertions required by the task specification.
    """
    # Scaffold overlap check
    overlap = train_scaffolds.intersection(test_scaffolds)
    if overlap:
        raise AssertionError(
            f"Scaffold overlap between train and test sets: {len(overlap)} scaffolds."
        )

    # Ratio check (within 1 % absolute tolerance)
    actual_ratios = (
        train_len / total_len,
        val_len / total_len,
        test_len / total_len,
    )
    for actual, target, name in zip(
        actual_ratios, ratios, ("train", "val", "test")
    ):
        if abs(actual - target) > 0.01:
            raise AssertionError(
                f"{name} split ratio {actual:.3f} deviates >1 % from target {target:.3f}."
            )


# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate scaffold‑based 5×5 splits."
    )
    parser.add_argument(
        "--folds",
        type=int,
        default=5,
        help="Number of outer scaffold splits (default: 5).",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=5,
        help="Number of inner repeats per outer split (default: 5).",
    )
    parser.add_argument(
        "--ratios",
        type=float,
        nargs=3,
        default=[0.8, 0.1, 0.1],
        help="Train/val/test ratios (must sum to 1).",
    )
    args = parser.parse_args()

    # Validate ratio sum.
    if not abs(sum(args.ratios) - 1.0) < 1e-6:
        raise ValueError("Provided ratios must sum to 1.0")

    # Load processed dataset.
    processed_path = paths.data("processed", "filtered.csv")
    if not processed_path.is_file():
        raise FileNotFoundError(
            f"Processed dataset not found at {processed_path}. "
            "Run code/data/preprocess.py first."
        )
    df = pd.read_csv(processed_path)

    total_records = len(df)
    log.info(f"Loaded processed dataset with {total_records} records.")

    # Compute scaffolds once.
    log.info("Computing Murcko scaffolds for all molecules...")
    scaffold_series = df["smiles"].apply(murcko_scaffold)
    df["scaffold"] = scaffold_series

    # Map scaffold string -> list of row indices.
    scaffold_to_indices = defaultdict(list)
    for idx, scaf in enumerate(scaffold_series):
        scaffold_to_indices[scaf].append(idx)

    # Prepare output directory.
    splits_dir = paths.data("splits")
    splits_dir.mkdir(parents=True, exist_ok=True)

    # Outer seeds: 100‑104 → i = 1..5
    for i in range(1, args.folds + 1):
        outer_seed = 100 + (i - 1)
        for j in range(1, args.repeats + 1):
            inner_seed = 200 + (j - 1)

            # Combine seeds to obtain a deterministic RNG for this split.
            combined_seed = outer_seed * 1_000 + inner_seed
            rng = random.Random(combined_seed)

            train_idx, val_idx, test_idx = allocate_scaffolds(
                scaffold_to_indices,
                total_len=total_records,
                ratios=args.ratios,
                rng=rng,
            )

            # Extract dataframes.
            df_train = df.iloc[train_idx].drop(columns=["scaffold"])
            df_val = df.iloc[val_idx].drop(columns=["scaffold"])
            df_test = df.iloc[test_idx].drop(columns=["scaffold"])

            # Verify split constraints.
            train_scaffolds = set(df_train["smiles"].apply(murcko_scaffold))
            test_scaffolds = set(df_test["smiles"].apply(murcko_scaffold))
            verify_split(
                train_scaffolds,
                test_scaffolds,
                len(df_train),
                len(df_val),
                len(df_test),
                total_records,
                tuple(args.ratios),
            )

            # Print summary.
            print(
                f"Fold {i}, repeat {j}: "
                f"train {len(df_train)} ({len(train_scaffolds)} scaffolds), "
                f"val {len(df_val)} ({len(df_val['smiles'].apply(murcko_scaffold).unique())} scaffolds), "
                f"test {len(df_test)} ({len(test_scaffolds)} scaffolds)."
            )
            print(
                f"  Ratios → train {len(df_train)/total_records:.3f}, "
                f"val {len(df_val)/total_records:.3f}, "
                f"test {len(df_test)/total_records:.3f}"
            )

            # Write CSVs.
            train_path = splits_dir / f"train_{i}_{j}.csv"
            val_path = splits_dir / f"val_{i}_{j}.csv"
            test_path = splits_dir / f"test_{i}_{j}.csv"

            df_train.to_csv(train_path, index=False)
            df_val.to_csv(val_path, index=False)
            df_test.to_csv(test_path, index=False)

            # Validate each file against the contract schema.
            for split_name, split_df, split_path in [
                ("train", df_train, train_path),
                ("val", df_val, val_path),
                ("test", df_test, test_path),
            ]:
                try:
                    validate_rows(split_df)
                except (ValueError, ValidationError) as exc:
                    raise AssertionError(
                        f"Schema validation failed for {split_name} split "
                        f"(fold {i}, repeat {j}) at {split_path}: {exc}"
                    ) from exc

            log.info(
                f"Wrote split files for fold {i}, repeat {j} to {splits_dir}"
            )

    log.info("All scaffold splits generated successfully.")


if __name__ == "__main__":
    main()
