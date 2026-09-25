"""
Unit tests for src/analysis/fdr_validator.py (Task T022).
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path

from src.analysis.fdr_validator import (
    calculate_benjamini_hochberg,
    validate_q_values,
    run_fdr_validation
)


def test_calculate_benjamini_hochberg_basic():
    """Test basic BH calculation."""
    p_values = pd.Series([0.01, 0.02, 0.03, 0.04])
    q_values = calculate_benjamini_hochberg(p_values)

    # n=4
    # sorted p: 0.01, 0.02, 0.03, 0.04
    # ranks: 1, 2, 3, 4
    # raw q: 0.01*4/1=0.04, 0.02*4/2=0.04, 0.03*4/3=0.04, 0.04*4/4=0.04
    # after monotonicity: all 0.04
    expected = pd.Series([0.04, 0.04, 0.04, 0.04], index=p_values.index)

    pd.testing.assert_series_equal(q_values, expected)


def test_calculate_benjamini_hochberg_monotonicity():
    """Test that monotonicity correction is applied."""
    # p-values that would produce non-monotonic q without correction
    p_values = pd.Series([0.01, 0.05, 0.10, 0.20])
    q_values = calculate_benjamini_hochberg(p_values)

    # Check monotonicity
    assert (np.diff(q_values) >= -1e-9).all()


def test_validate_q_values_valid():
    """Test validation with correct q-values."""
    p_values = pd.Series([0.01, 0.02, 0.03, 0.04])
    q_values = calculate_benjamini_hochberg(p_values)

    df = pd.DataFrame({"p": p_values, "q": q_values})
    is_valid, messages = validate_q_values(df, p_col="p", q_col="q")

    assert is_valid
    assert any("PASSED" in msg for msg in messages)


def test_validate_q_values_invalid_q_less_than_p():
    """Test validation when q < p (impossible)."""
    p_values = pd.Series([0.01, 0.02])
    q_values = pd.Series([0.005, 0.015])  # q < p, invalid

    df = pd.DataFrame({"p": p_values, "q": q_values})
    is_valid, messages = validate_q_values(df, p_col="p", q_col="q")

    # Should fail because q < p violates BH property (q >= p)
    assert not is_valid


def test_validate_q_values_out_of_range():
    """Test validation when q > 1 or q < 0."""
    p_values = pd.Series([0.01, 0.02])
    q_values = pd.Series([1.5, 0.5])  # 1.5 > 1

    df = pd.DataFrame({"p": p_values, "q": q_values})
    is_valid, messages = validate_q_values(df, p_col="p", q_col="q")

    assert not is_valid
    assert any("outside the range" in msg for msg in messages)


def test_run_fdr_validation_integration():
    """Integration test: write temp file, run validation, check log."""
    p_values = pd.Series([0.01, 0.02, 0.03, 0.04])
    q_values = calculate_benjamini_hochberg(p_values)

    df = pd.DataFrame({
        "taxon": ["A", "B", "C", "D"],
        "maaslin2_p_value": p_values,
        "maaslin2_q_value": q_values
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test_input.tsv"
        output_path = Path(tmpdir) / "test_output.txt"

        df.to_csv(input_path, sep="\t", index=False)

        success = run_fdr_validation(input_path, output_path)

        assert success
        assert output_path.exists()

        with open(output_path, "r") as f:
            content = f.read()

        assert "PASSED" in content


def test_run_fdr_validation_missing_column():
    """Test validation when p-value column is missing."""
    df = pd.DataFrame({"taxon": ["A"], "wrong_col": [0.01]})

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test_input.tsv"
        output_path = Path(tmpdir) / "test_output.txt"

        df.to_csv(input_path, sep="\t", index=False)

        success = run_fdr_validation(input_path, output_path)

        assert not success
        assert output_path.exists()

        with open(output_path, "r") as f:
            content = f.read()

        assert "ERROR" in content
        assert "not found" in content


def test_empty_dataframe():
    """Test BH calculation on empty series."""
    p_values = pd.Series([], dtype=float)
    q_values = calculate_benjamini_hochberg(p_values)

    assert len(q_values) == 0


def test_single_value():
    """Test BH calculation on single p-value."""
    p_values = pd.Series([0.05])
    q_values = calculate_benjamini_hochberg(p_values)

    # n=1: q = p * 1 / 1 = p
    expected = pd.Series([0.05], index=p_values.index)
    pd.testing.assert_series_equal(q_values, expected)