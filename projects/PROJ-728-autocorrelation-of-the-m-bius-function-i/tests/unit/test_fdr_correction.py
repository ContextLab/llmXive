"""
Unit tests for ``code.fdr_correction``.
"""

import pathlib
import tempfile

import pandas as pd
import pytest

# Import the module under test.
from fdr_correction import _apply_bh_correction, _write_stats, _read_stats, INPUT_CSV

def test_apply_bh_correction_basic():
    """Check that the BH correction adds the column and produces sensible values."""
    # Create a tiny DataFrame with known p‑values.
    df = pd.DataFrame(
        {
            "interval_start": [1, 2, 3],
            "interval_length": [1000, 1000, 1000],
            "lag": [1, 2, 3],
            "autocorrelation": [0.1, -0.2, 0.05],
            "p_value": [0.01, 0.20, 0.04],
        }
    )
    df_corrected = _apply_bh_correction(df.copy())

    # The new column must exist.
    assert "adjusted_p_value" in df_corrected.columns

    # The adjusted p‑values should be >= the raw ones and ≤ 1.
    assert (df_corrected["adjusted_p_value"] >= df_corrected["p_value"]).all()
    assert (df_corrected["adjusted_p_value"] <= 1.0).all()

    # At least one adjusted p‑value must be ≤ 0.05 (the first entry).
    assert (df_corrected["adjusted_p_value"] <= 0.05).any()

def test_apply_bh_correction_empty_dataframe():
    """The function must handle an empty CSV (header only) gracefully."""
    empty_df = pd.DataFrame(
        columns=[
            "interval_start",
            "interval_length",
            "lag",
            "autocorrelation",
            "p_value",
            "adjusted_p_value",
            "ci_lower",
            "ci_upper",
            "zero_count",
            "sensitivity_flag",
            "theoretical_variance",
        ]
    )
    # The function should add the column without raising.
    result_df = _apply_bh_correction(empty_df.copy())
    assert "adjusted_p_value" in result_df.columns
    assert result_df.empty

def test_full_round_trip_write_and_read(tmp_path: pathlib.Path):
    """Write a CSV, run the main correction, and read it back."""
    # Prepare a temporary CSV file.
    csv_path = tmp_path / "temp_stats.csv"
    df = pd.DataFrame(
        {
            "interval_start": [10],
            "interval_length": [1000],
            "lag": [1],
            "autocorrelation": [0.0],
            "p_value": [0.03],
        }
    )
    _write_stats(df, csv_path)

    # Monkey‑patch the module‑level INPUT_CSV to point to our temp file.
    original_input = INPUT_CSV
    try:
        # Replace the constant for the duration of the test.
        import importlib
        import fdr_correction

        fdr_correction.INPUT_CSV = csv_path
        importlib.reload(fdr_correction)

        # Run the main function which reads, corrects, and writes back.
        fdr_correction.main()

        # Read back the file and verify the new column.
        df_out = pd.read_csv(csv_path)
        assert "adjusted_p_value" in df_out.columns
        # The adjusted p‑value must be ≤ 0.05 because the raw p is 0.03.
        assert df_out.loc[0, "adjusted_p_value"] <= 0.05
    finally:
        # Restore the original constant to avoid side effects.
        import fdr_correction

        fdr_correction.INPUT_CSV = original_input
        importlib.reload(fdr_correction)