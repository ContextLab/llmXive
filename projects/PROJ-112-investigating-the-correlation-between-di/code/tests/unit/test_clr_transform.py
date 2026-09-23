"""
Unit tests for the CLR transformation module.
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path

from src.preprocessing.clr_transform import (
    add_pseudocount,
    apply_clr,
    validate_output,
    identify_taxon_columns,
    run_clr_transform
)


@pytest.fixture
def sample_taxon_df():
    """Create a sample DataFrame with taxon abundances."""
    data = {
        "sample_id": ["S1", "S2", "S3"],
        "cohort_id": ["AGP", "UKBB", "AGP"],
        "fiber_g_day": [25.0, 40.0, 15.0],
        "read_count": [10000, 50000, 20000],
        "taxon_A": [0.1, 0.2, 0.0],  # Includes a zero
        "taxon_B": [0.5, 0.3, 0.6],
        "taxon_C": [0.4, 0.5, 0.4]
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_input_file(sample_taxon_df):
    """Create a temporary input TSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
        sample_taxon_df.to_csv(f, sep='\t', index=False)
        return f.name


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_identify_taxon_columns(sample_taxon_df):
    """Test that taxon columns are correctly identified."""
    taxon_cols = identify_taxon_columns(sample_taxon_df)
    assert set(taxon_cols) == {"taxon_A", "taxon_B", "taxon_C"}


def test_add_pseudocount(sample_taxon_df):
    """Test that pseudocount is added correctly and zeros are handled."""
    pseudocount = 1e-6
    df_transformed = add_pseudocount(sample_taxon_df, ["taxon_A", "taxon_B", "taxon_C"], pseudocount)

    # Check that zeros became pseudocount
    assert df_transformed.loc[2, "taxon_A"] == pseudocount
    # Check that non-zeros increased by pseudocount
    assert df_transformed.loc[0, "taxon_A"] == 0.1 + pseudocount
    # Metadata should be unchanged
    assert df_transformed.loc[0, "fiber_g_day"] == 25.0


def test_apply_clr(sample_taxon_df):
    """Test CLR transformation logic."""
    # First add pseudocount
    df_with_pc = add_pseudocount(sample_taxon_df, ["taxon_A", "taxon_B", "taxon_C"], 1e-6)
    # Then apply CLR
    df_clr = apply_clr(df_with_pc, ["taxon_A", "taxon_B", "taxon_C"])

    # Property: Sum of CLR values for a sample should be 0 (approx due to float precision)
    for idx, row in df_clr.iterrows():
        clr_sum = row["taxon_A"] + row["taxon_B"] + row["taxon_C"]
        assert np.isclose(clr_sum, 0.0, atol=1e-6), f"CLR sum for sample {idx} is not zero: {clr_sum}"


def test_validate_output_valid(sample_taxon_df):
    """Test validation on a valid DataFrame."""
    df_with_pc = add_pseudocount(sample_taxon_df, ["taxon_A", "taxon_B", "taxon_C"], 1e-6)
    df_clr = apply_clr(df_with_pc, ["taxon_A", "taxon_B", "taxon_C"])

    # Mock logger
    class MockLogger:
        def error(self, msg): pass
        def info(self, msg): pass

    is_valid, msg = validate_output(df_clr, ["taxon_A", "taxon_B", "taxon_C"], MockLogger())
    assert is_valid is True


def test_validate_output_nan():
    """Test validation detects NaN."""
    data = {
        "sample_id": ["S1"],
        "cohort_id": ["AGP"],
        "fiber_g_day": [25.0],
        "read_count": [10000],
        "taxon_A": [np.nan],
        "taxon_B": [0.5],
        "taxon_C": [0.4]
    }
    df = pd.DataFrame(data)
    class MockLogger:
        def error(self, msg): pass
        def info(self, msg): pass

    is_valid, msg = validate_output(df, ["taxon_A", "taxon_B", "taxon_C"], MockLogger())
    assert is_valid is False
    assert "NaN" in msg


def test_run_clr_transform_integration(temp_input_file, temp_output_dir):
    """Integration test for the full pipeline."""
    output_file = os.path.join(temp_output_dir, "clr_output.tsv")
    log_file = os.path.join(temp_output_dir, "validation_log.txt")

    success = run_clr_transform(
        input_path=temp_input_file,
        output_path=output_file,
        validation_log_path=log_file,
        pseudocount=1e-6
    )

    assert success is True
    assert os.path.exists(output_file)
    assert os.path.exists(log_file)

    # Verify output content
    df_out = pd.read_csv(output_file, sep='\t')
    assert "taxon_A" in df_out.columns
    # Verify sum is approx zero
    for idx, row in df_out.iterrows():
        assert np.isclose(row["taxon_A"] + row["taxon_B"] + row["taxon_C"], 0.0, atol=1e-5)

def test_run_clr_transform_missing_input():
    """Test that the script fails loudly on missing input."""
    success = run_clr_transform(
        input_path="nonexistent_file.tsv",
        output_path="output.tsv",
        validation_log_path="log.txt"
    )
    assert success is False