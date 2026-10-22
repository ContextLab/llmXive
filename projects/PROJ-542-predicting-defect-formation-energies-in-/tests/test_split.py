"""
tests/test_split.py
-------------------

Unit tests for the ``src.models.split`` module.  They verify that:
  * The split respects the 80 % / 20 % proportion (within one row tolerance).
  * No composition appears in both the training and test CSVs.
  * The log file and checksum files are created.
"""

import pathlib

import pandas as pd
import pytest

from src.models.split import split_dataset, main

def _create_dummy_features(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a minimal but realistic features CSV."""
    data = {
        "composition": ["ABX3", "ABX3", "ABX3", "ABX3", "ABX3",
                        "A2BX4", "A2BX4", "A2BX4", "A2BX4", "A2BX4",
                        "A3BX5", "A3BX5", "A3BX5", "A3BX5", "A3BX5"],
        "formation_energy": [1.0] * 15,
    }
    # Add the required descriptor columns (dummy numeric values).
    for site in ["A", "B", "X"]:
        for desc in [
            "atomic_radius",
            "electronegativity",
            "oxidation_state",
            "valence_electrons",
        ]:
            col = f"{site}_{desc}"
            data[col] = [0.1] * 15
    df = pd.DataFrame(data)
    features_path = tmp_path / "features.csv"
    df.to_csv(features_path, index=False)
    return features_path

def test_split_dataset_basic(tmp_path: pathlib.Path):
    features_path = _create_dummy_features(tmp_path)
    train_path = tmp_path / "train.csv"
    test_path = tmp_path / "test.csv"

    train_df, test_df = split_dataset(
        features_path=features_path,
        train_path=train_path,
        test_path=test_path,
        test_size=0.2,
        random_state=42,
    )

    # Verify CSV files were written.
    assert train_path.is_file()
    assert test_path.is_file()

    # Proportion check (allow rounding differences of one row).
    total = len(train_df) + len(test_df)
    expected_test = int(round(total * 0.2))
    assert abs(len(test_df) - expected_test) <= 1

    # No composition overlap.
    assert set(train_df["composition"]).isdisjoint(set(test_df["composition"]))

def test_cli_execution(tmp_path: pathlib.Path):
    # Build dummy input.
    features_path = _create_dummy_features(tmp_path)
    train_path = tmp_path / "train.csv"
    test_path = tmp_path / "test.csv"

    # Run the CLI via the module's ``main`` function.
    # Monkey‑patch ``sys.argv``.
    import sys

    original_argv = sys.argv
    sys.argv = [
        "src.models.split",
        str(features_path),
        str(train_path),
        str(test_path),
    ]
    try:
        main()
    finally:
        sys.argv = original_argv

    # Verify artefacts.
    assert train_path.is_file()
    assert test_path.is_file()
    assert pathlib.Path("data/processed/split.log").is_file()
    assert pathlib.Path("data/checksums/train.sha256").is_file()
    assert pathlib.Path("data/checksums/test.sha256").is_file()