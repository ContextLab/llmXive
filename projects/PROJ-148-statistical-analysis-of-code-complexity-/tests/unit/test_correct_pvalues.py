"""
Unit tests for code/modeling/correct_pvalues.py
"""
from __future__ import annotations

import pathlib
import tempfile
import pandas as pd
import pytest

from modeling.correct_pvalues import (
    load_pvalues,
    apply_bh_correction,
    compute_fdp,
    save_corrected,
    DEFAULT_INPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    ALPHA
)


def test_load_pvalues_missing_file():
    """Test that load_pvalues raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_pvalues(pathlib.Path("non_existent_file.csv"))


def test_load_pvalues_missing_column():
    """Test that load_pvalues raises ValueError if p_value column is missing."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        df = pd.DataFrame({"feature": ["a", "b"], "value": [0.1, 0.2]})
        df.to_csv(tmp.name, index=False)
        tmp_path = pathlib.Path(tmp.name)

    with pytest.raises(ValueError, match="must contain a 'p_value' column"):
        load_pvalues(tmp_path)


def test_apply_bh_correction():
    """Test that apply_bh_correction adds expected columns."""
    df = pd.DataFrame({
        "feature": ["f1", "f2", "f3"],
        "p_value": [0.01, 0.04, 0.10]
    })
    result = apply_bh_correction(df, alpha=0.05)
    assert "p_value_corrected" in result.columns
    assert "rejected" in result.columns
    assert len(result) == len(df)


def test_compute_fdp():
    """Test FDP computation."""
    df_rejected = pd.DataFrame({"rejected": [True, True, False]})
    assert compute_fdp(df_rejected) == pytest.approx(2/3)

    df_no_rejected = pd.DataFrame({"rejected": [False, False]})
    assert compute_fdp(df_no_rejected) == 0.0

    df_empty = pd.DataFrame({"rejected": []})
    assert compute_fdp(df_empty) == 0.0


def test_compute_fdp_missing_column():
    """Test that compute_fdp raises ValueError if rejected column is missing."""
    df = pd.DataFrame({"p_value": [0.01]})
    with pytest.raises(ValueError, match="must contain a 'rejected' column"):
        compute_fdp(df)


def test_save_corrected(tmp_path):
    """Test that save_corrected writes a CSV file."""
    df = pd.DataFrame({
        "feature": ["f1"],
        "p_value": [0.01],
        "p_value_corrected": [0.01],
        "rejected": [True]
    })
    out_file = tmp_path / "test_output.csv"
    save_corrected(df, out_file)
    assert out_file.exists()
    loaded = pd.read_csv(out_file)
    assert len(loaded) == 1
    assert "p_value_corrected" in loaded.columns
    assert "rejected" in loaded.columns
