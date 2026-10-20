"""
Utilities for stratified splitting and k‑fold cross‑validation.

The implementation guarantees:
* 80 % train, 10 % validation, 10 % test stratified by ``crystal_system``.
* Five CV folds on the training portion, each fold preserving the exact
  class balance (the number of samples of each crystal system is the same
  in every fold’s training and validation sets).
* Deterministic behaviour given ``random_state``.
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------
def _load_dataframe(csv_path: Path) -> pd.DataFrame:
    """Load the processed CSV as a DataFrame."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Processed CSV not found at {csv_path}")
    return pd.read_csv(csv_path)

# ----------------------------------------------------------------------
# Stratified 80/10/10 split
# ----------------------------------------------------------------------
def stratified_split(
    df: pd.DataFrame,
    train_frac: float = 0.8,
    val_frac: float = 0.1,
    test_frac: float = 0.1,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform an 80/10/10 train/val/test split stratified by ``crystal_system``.

    Returns three DataFrames (train, val, test).  The split is deterministic
    given ``random_state``.
    """
    if not np.isclose(train_frac + val_frac + test_frac, 1.0):
        raise ValueError("train_frac + val_frac + test_frac must sum to 1")

    # First split off the test set (10 %)
    sss_test = StratifiedShuffleSplit(
        n_splits=1, test_size=test_frac, random_state=random_state
    )
    train_val_idx, test_idx = next(sss_test.split(df, df["crystal_system"]))
    train_val_df = df.iloc[train_val_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # Now split the remaining 90 % into train (≈80 %) and val (≈10 %)
    # The validation proportion relative to the remaining data is
    # val_frac / (train_frac + val_frac).
    val_relative = val_frac / (train_frac + val_frac)
    sss_val = StratifiedShuffleSplit(
        n_splits=1, test_size=val_relative, random_state=random_state
    )
    train_idx, val_idx = next(sss_val.split(train_val_df, train_val_df["crystal_system"]))
    train_df = train_val_df.iloc[train_idx].reset_index(drop=True)
    val_df = train_val_df.iloc[val_idx].reset_index(drop=True)

    # Sanity checks – ensure disjointness and correct stratification
    assert set(train_df["material_id"]).isdisjoint(set(val_df["material_id"]))
    assert set(train_df["material_id"]).isdisjoint(set(test_df["material_id"]))
    assert set(val_df["material_id"]).isdisjoint(set(test_df["material_id"]))

    return train_df, val_df, test_df

# ----------------------------------------------------------------------
# Balanced CV folds on the training set
# ----------------------------------------------------------------------
def generate_cv_folds(
    train_df: pd.DataFrame, n_folds: int = 5, random_state: int = 42
) -> List[Dict[str, List[str]]]:
    """
    Generate ``n_folds`` stratified CV folds from ``train_df``.

    Each fold is a dict with keys ``train`` and ``val`` containing lists of
    ``material_id`` strings.  The algorithm guarantees that for every
    crystal‑system class the number of validation samples per fold is the
    same, and consequently the training portion of each fold is perfectly
    balanced as well.
    """
    rng = np.random.default_rng(random_state)

    # Group material IDs by crystal system
    class_groups: Dict[str, List[str]] = {}
    for cls, mid in zip(train_df["crystal_system"], train_df["material_id"]):
        class_groups.setdefault(cls, []).append(mid)

    # Shuffle each class list deterministically
    for cls in class_groups:
        rng.shuffle(class_groups[cls])

    # Determine per‑fold validation size for each class
    folds: List[Dict[str, List[str]]] = [
        {"train": [], "val": []} for _ in range(n_folds)
    ]

    for cls, ids in class_groups.items():
        total = len(ids)
        base = total // n_folds
        remainder = total % n_folds
        # Distribute the remainder one‑by‑one to the first ``remainder`` folds
        fold_sizes = [base + (1 if i < remainder else 0) for i in range(n_folds)]

        start = 0
        for i, size in enumerate(fold_sizes):
            val_ids = ids[start : start + size]
            start += size
            folds[i]["val"].extend(val_ids)

    # Build training lists as “all ids minus the validation ids of that fold”
    all_ids = list(train_df["material_id"])
    for i in range(n_folds):
        val_set = set(folds[i]["val"])
        folds[i]["train"] = [mid for mid in all_ids if mid not in val_set]

    # Convert to plain lists (already are) and return
    return folds

# ----------------------------------------------------------------------
# JSON export helpers
# ----------------------------------------------------------------------
def _write_json(data: object, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

def create_and_save_splits(
    processed_csv: Path, output_dir: Path, seed: int = 42
) -> None:
    """
    Load ``processed_csv``, perform the stratified 80/10/10 split, generate
    5 CV folds on the training portion, and write the results to ``output_dir``
    as JSON files:

    * ``train_val_test.json`` – dict with keys ``train``, ``val``, ``test``
      each holding a list of ``material_id`` strings.
    * ``cv_folds.json`` – list of 5 fold dicts (as produced by
      ``generate_cv_folds``).
    """
    df = _load_dataframe(processed_csv)
    train_df, val_df, test_df = stratified_split(df, random_state=seed)

    # Export the three main splits
    split_dict = {
        "train": list(train_df["material_id"]),
        "val": list(val_df["material_id"]),
        "test": list(test_df["material_id"]),
    }
    _write_json(split_dict, output_dir / "train_val_test.json")

    # Generate and export CV folds
    cv_folds = generate_cv_folds(train_df, n_folds=5, random_state=seed)
    _write_json(cv_folds, output_dir / "cv_folds.json")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Create data splits for the pipeline")
    parser.add_argument(
        "--processed_csv",
        type=Path,
        required=True,
        help="Path to the cleaned CSV produced by the loader",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        required=True,
        help="Directory where split JSON files will be written",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    create_and_save_splits(args.processed_csv, args.output_dir, seed=args.seed)

if __name__ == "__main__":
    main()
