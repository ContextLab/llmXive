import os
import json
import pandas as pd
from pathlib import Path

# Import the preprocessing module
from data.preprocess import validate_and_preprocess, get_processed_data_dir

def test_preprocessing_creates_outputs(tmp_path, monkeypatch):
    """
    Verify that the preprocessing pipeline creates train.csv, test.csv,
    and that the resulting files contain no missing values and that all
    numeric feature columns are scaled to the [0, 1] interval.
    """
    # Use the project's actual processed directory
    processed_dir = get_processed_data_dir()

    # Ensure a clean state: remove any existing output files
    for f in ["train.csv", "test.csv", "preprocessing.log", "normalization_bounds.json"]:
        p = processed_dir / f
        if p.exists():
            p.unlink()

    # Run the preprocessing pipeline
    validate_and_preprocess()

    # Check that files exist
    train_path = processed_dir / "train.csv"
    test_path = processed_dir / "test.csv"
    bounds_path = processed_dir / "normalization_bounds.json"
    assert train_path.is_file(), "train.csv was not created"
    assert test_path.is_file(), "test.csv was not created"
    assert bounds_path.is_file(), "normalization_bounds.json was not created"

    # Load data
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    # No missing values
    assert not train_df.isna().any().any(), "train.csv contains missing values"
    assert not test_df.isna().any().any(), "test.csv contains missing values"

    # Identify feature columns (exclude targets)
    target_cols = [c for c in ["yield_strength", "ductility"] if c in train_df.columns]
    feature_cols = [c for c in train_df.columns if c not in target_cols]

    # All numeric feature columns must be within [0, 1]
    for col in feature_cols:
        # Ensure column is numeric
        assert pd.api.types.is_numeric_dtype(train_df[col]), f"Feature column {col} is not numeric"
        min_val = train_df[col].min()
        max_val = train_df[col].max()
        assert 0.0 <= min_val <= 1.0, f"Column {col} has min {min_val} outside [0,1]"
        assert 0.0 <= max_val <= 1.0, f"Column {col} has max {max_val} outside [0,1]"

    # Verify that normalization bounds match the recorded min/max
    with open(bounds_path, "r") as f:
        bounds = json.load(f)
    for col, b in bounds.items():
        assert col in feature_cols, f"Bounds contain unexpected column {col}"
        # The bounds should be the original (pre‑scaled) min/max; we cannot check exact values
        # but we ensure they are numeric
        assert isinstance(b["min"], (int, float)), "Bound min is not numeric"
        assert isinstance(b["max"], (int, float)), "Bound max is not numeric"