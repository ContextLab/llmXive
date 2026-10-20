"""
Unit tests for ``src/training/split.py``.

The tests construct a tiny synthetic DataFrame with two crystal systems
and verify that:
  * the 80/10/10 split respects the crystal‑system proportions,
  * no ``material_id`` appears in more than one split,
  * the five CV folds are stratified (each fold contains roughly the same
    proportion of each crystal system), and
  * repeated calls with the same seed produce identical splits.
"""
import pandas as pd
from pathlib import Path

from src.training.split import (
    stratified_split,
    generate_cv_folds,
    create_and_save_splits,
)

def _make_fixture() -> pd.DataFrame:
    # 20 rows, 2 crystal systems (cubic and hexagonal) equally represented
    rows = []
    for i in range(10):
        rows.append(
            {
                "material_id": f"cubic_{i}",
                "crystal_system": "cubic",
            }
        )
    for i in range(10):
        rows.append(
            {
                "material_id": f"hex_{i}",
                "crystal_system": "hexagonal",
            }
        )
    return pd.DataFrame(rows)

def test_stratified_split_is_deterministic(tmp_path: Path):
    df = _make_fixture()
    train1, val1, test1 = stratified_split(df, random_state=123)
    train2, val2, test2 = stratified_split(df, random_state=123)

    assert train1["material_id"].tolist() == train2["material_id"].tolist()
    assert val1["material_id"].tolist() == val2["material_id"].tolist()
    assert test1["material_id"].tolist() == test2["material_id"].tolist()

    # 80 % of 20 → 16 rows, split proportionally (8 cubic, 8 hex)
    assert len(train1) == 16
    assert train1["crystal_system"].value_counts().to_dict() == {"cubic": 8, "hexagonal": 8}

    # 10 % → 2 rows each for val and test (1 cubic, 1 hex)
    assert len(val1) == 2
    assert len(test1) == 2
    assert set(val1["crystal_system"]) == {"cubic", "hexagonal"}
    assert set(test1["crystal_system"]) == {"cubic", "hexagonal"}

    # Disjointness
    assert set(train1["material_id"]).isdisjoint(set(val1["material_id"]))
    assert set(train1["material_id"]).isdisjoint(set(test1["material_id"]))
    assert set(val1["material_id"]).isdisjoint(set(test1["material_id"]))

def test_generate_cv_folds_is_stratified_and_reproducible():
    df = _make_fixture()
    train_df, _, _ = stratified_split(df, random_state=42)
    folds1 = generate_cv_folds(train_df, n_folds=5, random_state=99)
    folds2 = generate_cv_folds(train_df, n_folds=5, random_state=99)

    # Same seed → identical folds
    assert folds1 == folds2

    # Each fold should preserve crystal‑system proportions (approximately)
    for fold in folds1:
        # training portion of a fold is 80 % of the original train set (16 rows)
        # → 12 or 13 rows depending on rounding, but the ratio should stay ~1:1
        train_counts = pd.Series(fold["train"]).map(
            lambda mid: "cubic" if mid.startswith("cubic_") else "hexagonal"
        ).value_counts()
        # Because the original train set is perfectly balanced, each fold's train
        # portion must also be balanced.
        assert train_counts["cubic"] == train_counts["hexagonal"]

        # Validation portion is the complement; also balanced.
        val_counts = pd.Series(fold["val"]).map(
            lambda mid: "cubic" if mid.startswith("cubic_") else "hexagonal"
        ).value_counts()
        assert val_counts["cubic"] == val_counts["hexagonal"]

def test_create_and_save_splits_writes_files(tmp_path: Path):
    df = _make_fixture()
    csv_path = tmp_path / "materials_processed.csv"
    df.to_csv(csv_path, index=False)

    out_dir = tmp_path / "splits"
    create_and_save_splits(csv_path, out_dir, seed=7)

    # Expect two JSON files
    assert (out_dir / "train_val_test.json").is_file()
    assert (out_dir / "cv_folds.json").is_file()

    # Load and perform a sanity check on the content
    import json

    with (out_dir / "train_val_test.json").open() as f:
        splits = json.load(f)
    assert set(splits["train"]).isdisjoint(set(splits["val"]))
    assert set(splits["train"]).isdisjoint(set(splits["test"]))
    assert set(splits["val"]).isdisjoint(set(splits["test"]))
    assert len(splits["train"]) + len(splits["val"]) + len(splits["test"]) == 20

    with (out_dir / "cv_folds.json").open() as f:
        cv = json.load(f)
    assert isinstance(cv, list) and len(cv) == 5
    for fold in cv:
        assert set(fold["train"]).isdisjoint(set(fold["val"]))
        # Union of train and val for a fold should equal the full training set
        assert set(fold["train"]).union(set(fold["val"])) == set(splits["train"])