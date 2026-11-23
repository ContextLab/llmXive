"""
Unit test for the Random Forest training script (code/models/rf.py).

This test creates a minimal training CSV file with the required descriptor
columns and a target column, invokes the script's CLI entry point, and
verifies that:
  1. The model pickle file is created at the expected location.
  2. The loaded model has a ``feature_importances_`` attribute of length 6.
The test cleans up any files it creates to avoid side‑effects on other tests.
"""
import os
from pathlib import Path

import joblib
import pandas as pd
import pytest

# Import the CLI entry point from the RF module
from models.rf import main as rf_main


@pytest.fixture
def dummy_training_data():
    """
    Create a temporary training CSV with the six required descriptor columns
    and a ``target`` column. The file is placed in the project's expected
    location ``data/processed/train.csv``.
    """
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    train_path = processed_dir / "train.csv"

    # Minimal synthetic dataset – values are arbitrary but valid.
    df = pd.DataFrame(
        {
            "mw": [120.5, 250.0, 180.2],
            "logp": [1.1, 2.4, 1.8],
            "tpsa": [35.0, 55.2, 42.1],
            "hba": [2, 3, 2],
            "hbd": [1, 0, 1],
            "rotatable_bonds": [3, 5, 4],
            "target": [0.75, 1.20, 0.95],
        }
    )
    df.to_csv(train_path, index=False)
    yield train_path
    # Cleanup after test
    if train_path.is_file():
        train_path.unlink()


def test_rf_training_cli(dummy_training_data):
    """
    Execute the Random Forest training script and verify the output model.
    """
    # Run the CLI entry point which reads ``data/processed/train.csv``
    rf_main()

    model_path = Path("code/models/rf.pkl")
    assert model_path.is_file(), "RF model pickle file was not created."

    # Load the model and check feature importances
    model = joblib.load(model_path)
    assert hasattr(model, "feature_importances_"), "Model lacks feature_importances_"
    assert (
        len(model.feature_importances_) == 6
    ), "Expected 6 feature importances (one per descriptor)."

    # Clean up the generated model file
    try:
        model_path.unlink()
    except OSError:
        pass

# Ensure that the test does not interfere with other fixtures or
# environment settings. No additional teardown is required because the
# fixture handles cleanup of the temporary CSV file.