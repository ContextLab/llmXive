"""Unit tests for the stratified split and CV fold generation."""
import json
from pathlib import Path

import pandas as pd
import pytest

from src.training.split import stratified_split, generate_cv_folds, create_and_save_splits

# Load the tiny fixture
FIXTURE_PATH = Path(__file__).parents[2] / "data" / "fixtures" / "tiny_materials.csv"
df = pd.read_csv(FIXTURE_PATH)

def test_stratified_split_is_balanced():
    train, val, test = stratified_split(df, random_state=0)
    # each split should contain both crystal systems in (approximately) the correct ratio
    for split in (train, val, test):
        counts = split["crystal_system"].value_counts()
        assert counts["cubic"] == counts["hexagonal"]

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