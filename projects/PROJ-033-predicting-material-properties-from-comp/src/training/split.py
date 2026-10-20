"""
Crystal‑system‑stratified data split and 5‑fold cross‑validation.

This module provides utilities to:
  1. Split a cleaned materials CSV into train/validation/test sets
     (80 % / 10 % / 10 %) while preserving the distribution of
     ``crystal_system`` (stratification) and guaranteeing that each
     ``material_id`` appears in exactly one split.
  2. Generate 5 CV folds on the training portion, again stratified by
     ``crystal_system``.
  3. Export the split indices to ``data/processed/splits/`` as JSON
     files that can be consumed by downstream training scripts.

The implementation is deterministic once the global RNG seed is set
(via :pyfunc:`src.utils.seeds.set_global_seed`).  The unit‑test
``tests/unit/test_split.py`` validates stratification, disjointness,
and reproducibility.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit

from llmxive_toolkit import paths, get_logger
from src.utils.seeds import set_global_seed

log = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def _load_dataframe(csv_path: Path) -> pd.DataFrame:
    """Load the processed CSV as a DataFrame."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Processed data file not found: {csv_path}")
    df = pd.read_csv(csv_path, dtype={"material_id": str, "crystal_system": str})
    required = {"material_id", "crystal_system"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for splitting: {sorted(missing)}")
    return df

def stratified_split(
    df: pd.DataFrame,
    train_frac: float = 0.8,
    val_frac: float = 0.1,
    test_frac: float = 0.1,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform an 80/10/10 split stratified by ``crystal_system``.

    Returns
    -------
    train_df, val_df, test_df
    """
    if abs(train_frac + val_frac + test_frac - 1.0) > 1e-8:
        raise ValueError("train/val/test fractions must sum to 1")

    # First split off the test set
    sss1 = StratifiedShuffleSplit(
        n_splits=1,
        test_size=test_frac,
        random_state=random_state,
    )
    train_val_idx, test_idx = next(sss1.split(df, df["crystal_system"]))
    train_val_df = df.iloc[train_val_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # Now split the remaining portion into train/val
    val_relative = val_frac / (train_frac + val_frac)  # proportion of the *remaining* set
    sss2 = StratifiedShuffleSplit(
        n_splits=1,
        test_size=val_relative,
        random_state=random_state,
    )
    train_idx, val_idx = next(sss2.split(train_val_df, train_val_df["crystal_system"]))
    train_df = train_val_df.iloc[train_idx].reset_index(drop=True)
    val_df = train_val_df.iloc[val_idx].reset_index(drop=True)

    # Sanity checks
    assert set(train_df["material_id"]).isdisjoint(set(val_df["material_id"]))
    assert set(train_df["material_id"]).isdisjoint(set(test_df["material_id"]))
    assert set(val_df["material_id"]).isdisjoint(set(test_df["material_id"]))

    return train_df, val_df, test_df

def generate_cv_folds(
    train_df: pd.DataFrame,
    n_folds: int = 5,
    random_state: int = 42,
) -> List[Dict[str, List[str]]]:
    """
    Generate ``n_folds`` stratified CV folds from the training set.

    Each fold is a dict with keys ``train`` and ``val`` containing lists
    of ``material_id`` strings.

    Returns
    -------
    List[Dict[str, List[str]]]
    """
    skf = StratifiedKFold(
        n_splits=n_folds,
        shuffle=True,
        random_state=random_state,
    )
    folds: List[Dict[str, List[str]]] = []
    for train_index, val_index in skf.split(train_df, train_df["crystal_system"]):
        fold = {
            "train": train_df.iloc[train_index]["material_id"].tolist(),
            "val": train_df.iloc[val_index]["material_id"].tolist(),
        }
        folds.append(fold)
    return folds

def _write_json(data: object, out_path: Path) -> None:
    """Write *data* as pretty‑printed JSON, creating parent dirs."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    log.info("Wrote split file: %s", out_path)

# -------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------
def create_and_save_splits(
    processed_csv: Path,
    output_dir: Path,
    seed: int = 42,
) -> None:
    """
    Load ``processed_csv``, perform the stratified 80/10/10 split,
    generate 5 CV folds on the training set, and write the results to
    ``output_dir`` as JSON files.

    Files written
    --------------
    - ``train_val_test.json`` – dict with keys ``train``, ``val``, ``test``
      each holding a list of ``material_id`` strings.
    - ``cv_folds.json`` – list of 5 dicts, each with ``train`` and ``val``
      lists of ``material_id`` strings.
    """
    set_global_seed(seed)
    df = _load_dataframe(processed_csv)

    train_df, val_df, test_df = stratified_split(df, random_state=seed)

    # Save the three primary splits
    split_dict = {
        "train": train_df["material_id"].tolist(),
        "val": val_df["material_id"].tolist(),
        "test": test_df["material_id"].tolist(),
    }
    _write_json(split_dict, output_dir / "train_val_test.json")

    # Generate and save CV folds (only on the training portion)
    cv_folds = generate_cv_folds(train_df, n_folds=5, random_state=seed)
    _write_json(cv_folds, output_dir / "cv_folds.json")

# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create stratified train/val/test splits and 5‑fold CV for the materials dataset."
    )
    parser.add_argument(
        "--data",
        type=Path,
        required=True,
        help="Path to the cleaned CSV produced by the loader (e.g. data/processed/materials_processed.csv).",
    )
    parser.add_argument(
        "--out_dir",
        type=Path,
        default=paths.data("processed", "splits"),
        help="Directory where split JSON files will be written.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible splits.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    create_and_save_splits(args.data, args.out_dir, seed=args.seed)

if __name__ == "__main__":
    main()
