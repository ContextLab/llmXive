"""Unit tests for the T012 exclusion logic in code/preprocessing.py."""

import numpy as np
import pandas as pd
import pytest

from code.preprocessing import exclude_invalid_rows, _numeric_descriptor_columns


def _make_df():
    return pd.DataFrame({
        "smiles": ["C", "CC", "c1ccccc1", "CCO", "CCC"],
        "conductivity": [1e-5, 0.1, np.nan, -1e-3, 1e-2],
        "aromatic_ring_count": [0, 0, 1, 0, 0],
        "conjugation_path_length": [0, 0, 2, np.nan, 0],
        "mol_weight": [16.0, 30.0, 78.0, 46.0, np.inf],
    })


def test_missing_conductivity_counted():
    df = _make_df()
    clean, log = exclude_invalid_rows(df)
    # NaN and negative conductivity rows are excluded
    assert log["missing_conductivity"] == 2
    assert "missing_conductivity" in log and "invalid_descriptors" in log


def test_invalid_descriptors_counted():
    df = _make_df()
    clean, log = exclude_invalid_rows(df)
    # CCO has NaN descriptor, CCC has inf descriptor -> invalid descriptors
    assert log["invalid_descriptors"] == 2


def test_clean_rows_are_valid():
    df = _make_df()
    clean, log = exclude_invalid_rows(df)
    assert len(clean) == 1
    assert clean.iloc[0]["smiles"] == "CC"
    assert log["retained"] == len(clean)
    assert log["total_input"] == 5
    assert log["total_excluded"] == 4
    # No NaN or non-finite values remain in the numeric columns
    num = clean.drop(columns=["smiles"])
    assert not num.isna().any().any()
    assert np.isfinite(num.to_numpy(dtype=float)).all()


def test_missing_target_column_raises():
    df = pd.DataFrame({"smiles": ["C"], "x": [1.0]})
    with pytest.raises(ValueError):
        exclude_invalid_rows(df)


def test_descriptor_column_detection():
    df = _make_df()
    cols = _numeric_descriptor_columns(df, "conductivity")
    assert set(cols) == {"aromatic_ring_count", "conjugation_path_length", "mol_weight"}


def test_all_missing_target_raises_nowhere_but_returns_empty():
    df = pd.DataFrame({"smiles": ["C"], "conductivity": [np.nan], "x": [1.0]})
    clean, log = exclude_invalid_rows(df)
    assert len(clean) == 0
    assert log["missing_conductivity"] == 1