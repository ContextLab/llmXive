"""Unit tests for the stratified split and CV fold generation."""
import json
from pathlib import Path

import pandas as pd
import pytest

from src.training.split import stratified_split, generate_cv_folds, create_and_save_splits

# Load the tiny software‑validation fixture (never reported as study results)
FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "tiny_materials.csv"
df = pd.read_csv(FIXTURE_PATH)

def test_stratified_split_is_balanced():
    train, val, test = stratified_split(df, random_state=0)
    # each split should contain both crystal systems in (approximately) the correct ratio
    for split in (train, val, test):
        counts = split["crystal_system"].value_counts()
        assert counts["cubic"] == counts["hexagonal"]

def test_stratified_split_disjoint_and_complete():
    train, val, test = stratified_split(df, random_state=0)
    ids_train = set(train["material_id"])
    ids_val = set(val["material_id"])
    ids_test = set(test["material_id"])
    assert ids_train.isdisjoint(ids_val)
    assert ids_train.isdisjoint(ids_test)
    assert ids_val.isdisjoint(ids_test)
    assert ids_train | ids_val | ids_test == set(df["material_id"])

def test_stratified_split_reproducible():
    t1, v1, s1 = stratified_split(df, random_state=42)
    t2, v2, s2 = stratified_split(df, random_state=42)
    assert list(t1["material_id"]) == list(t2["material_id"])
    assert list(v1["material_id"]) == list(v2["material_id"])
    assert list(s1["material_id"]) == list(s2["material_id"])

def test_stratified_split_tiny_dataset_does_not_crash():
    """Regression test: singleton crystal‑system classes previously raised
    ValueError from StratifiedShuffleSplit (root cause of the failed run)."""
    tiny = pd.DataFrame(
        {
            "material_id": ["mp-1", "mp-2"],
            "formula": ["Fe2O3", "Si"],
            "band_gap": [1.7, 0.0],
            "hardness": [9.5, 0.0],
            "crystal_system": ["hexagonal", "cubic"],
        }
    )
    train, val, test = stratified_split(tiny, random_state=42)
    all_ids = set(train["material_id"]) | set(val["material_id"]) | set(test["material_id"])
    assert all_ids == {"mp-1", "mp-2"}
    # The train split must remain non‑empty so downstream training works.
    assert len(train) >= 1

def test_generate_cv_folds_is_stratified_and_reproducible():
    train, _, _ = stratified_split(df, random_state=0)
    folds = generate_cv_folds(train, n_folds=5, random_state=0)
    # each fold's validation set should have equal numbers of each crystal system
    for fold in folds:
        val_counts = pd.Series(fold["val"]).map(
            lambda mid: "cubic" if mid.startswith("cubic_") else "hexagonal"
        ).value_counts()
        assert val_counts["cubic"] == val_counts["hexagonal"]
        # training portion should also be balanced
        train_counts = pd.Series(fold["train"]).map(
            lambda mid: "cubic" if mid.startswith("cubic_") else "hexagonal"
        ).value_counts()
        assert train_counts["cubic"] == train_counts["hexagonal"]
    # reproducibility
    folds2 = generate_cv_folds(train, n_folds=5, random_state=0)
    assert folds == folds2

def test_create_and_save_splits_creates_files(tmp_path):
    out_dir = tmp_path / "splits"
    create_and_save_splits(FIXTURE_PATH, out_dir, seed=0)
    assert (out_dir / "train_val_test.json").exists()
    assert (out_dir / "cv_folds.json").exists()
    # Verify JSON structure
    with open(out_dir / "train_val_test.json") as f:
        data = json.load(f)
    assert set(data.keys()) == {"train", "val", "test"}
    with open(out_dir / "cv_folds.json") as f:
        folds = json.load(f)
    assert len(folds) == 5
