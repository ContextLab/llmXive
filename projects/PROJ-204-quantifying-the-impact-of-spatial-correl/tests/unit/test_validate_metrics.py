"""
Unit tests for the validate_metrics module.

Tests US-1 Scenario 3: validation logic to exclude samples with missing
performance metrics and log warnings with specific sample IDs.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import logging
from io import StringIO

from data.validate_metrics import (
    identify_missing_metrics,
    validate_and_filter_metrics,
    REQUIRED_PERFORMANCE_COLUMNS
)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with various missing value scenarios."""
    data = {
        'sample_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
        'PCE': [15.2, np.nan, 18.5, 16.8, np.nan],
        'J_sc': [22.1, 23.5, np.nan, 21.9, 24.0],
        'V_oc': [1.05, 1.10, 1.12, np.nan, 1.08],
        'other_column': ['a', 'b', 'c', 'd', 'e']
    }
    return pd.DataFrame(data)


@pytest.fixture
def valid_dataframe():
    """Create a DataFrame with no missing values."""
    data = {
        'sample_id': ['S001', 'S002', 'S003'],
        'PCE': [15.2, 18.5, 16.8],
        'J_sc': [22.1, 23.5, 21.9],
        'V_oc': [1.05, 1.10, 1.12],
        'other_column': ['a', 'b', 'c']
    }
    return pd.DataFrame(data)


def test_identify_missing_metrics_identifies_correct_samples(sample_dataframe):
    """Test that missing metrics are correctly identified."""
    valid_df, missing_ids, missing_details = identify_missing_metrics(
        sample_dataframe
    )

    # Should have 2 valid samples (S001 and S005)
    assert len(valid_df) == 2
    assert set(valid_df['sample_id'].tolist()) == {'S001', 'S005'}

    # Should have 3 samples with missing metrics
    assert len(missing_ids) == 3
    assert set(missing_ids) == {'S002', 'S003', 'S004'}

    # Check that missing details are descriptive
    assert len(missing_details) == 3
    for detail in missing_details:
        assert any(sid in detail for sid in missing_ids)


def test_identify_missing_metrics_no_missing(valid_dataframe):
    """Test behavior when there are no missing values."""
    valid_df, missing_ids, missing_details = identify_missing_metrics(
        valid_dataframe
    )

    assert len(valid_df) == 3
    assert len(missing_ids) == 0
    assert len(missing_details) == 0


def test_identify_missing_metrics_all_missing():
    """Test behavior when all samples have missing values."""
    data = {
        'sample_id': ['S001', 'S002'],
        'PCE': [np.nan, np.nan],
        'J_sc': [np.nan, np.nan],
        'V_oc': [np.nan, np.nan]
    }
    df = pd.DataFrame(data)

    valid_df, missing_ids, missing_details = identify_missing_metrics(df)

    assert len(valid_df) == 0
    assert len(missing_ids) == 2
    assert set(missing_ids) == {'S001', 'S002'}


def test_identify_missing_metrics_custom_columns():
    """Test with custom required columns."""
    data = {
        'sample_id': ['S001', 'S002', 'S003'],
        'PCE': [15.2, np.nan, 18.5],
        'J_sc': [22.1, 23.5, np.nan],
        'custom_metric': [100, 200, 300]
    }
    df = pd.DataFrame(data)

    valid_df, missing_ids, _ = identify_missing_metrics(
        df, required_columns=['PCE', 'custom_metric']
    )

    # S002 has missing PCE, S003 has all required columns
    assert len(valid_df) == 2
    assert set(valid_df['sample_id'].tolist()) == {'S001', 'S003'}
    assert missing_ids == ['S002']


def test_identify_missing_metrics_missing_column_in_schema():
    """Test behavior when required columns are missing from schema."""
    data = {
        'sample_id': ['S001', 'S002'],
        'PCE': [15.2, 18.5],
        'J_sc': [22.1, 23.5]
        # V_oc is missing from schema
    }
    df = pd.DataFrame(data)

    # Should warn but still work with available columns
    with pytest.warns(None) if hasattr(pytest, 'warns') else contextlib.nullcontext():
        valid_df, missing_ids, _ = identify_missing_metrics(df)

    # Both samples should be valid since PCE and J_sc are present
    assert len(valid_df) == 2


def test_validate_and_filter_metrics_integration():
    """Test the full validation and filtering workflow."""
    data = {
        'sample_id': ['S001', 'S002', 'S003', 'S004'],
        'PCE': [15.2, np.nan, 18.5, 16.8],
        'J_sc': [22.1, 23.5, np.nan, 21.9],
        'V_oc': [1.05, 1.10, 1.12, np.nan]
    }
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / 'input.csv'
        output_path = Path(tmpdir) / 'output.csv'

        df.to_csv(input_path, index=False)

        stats = validate_and_filter_metrics(
            str(input_path),
            str(output_path)
        )

        # Check statistics
        assert stats['total_samples'] == 4
        assert stats['valid_samples'] == 1
        assert stats['excluded_count'] == 3
        assert set(stats['excluded_sample_ids']) == {'S002', 'S003', 'S004'}

        # Check output file exists and has correct content
        assert output_path.exists()
        output_df = pd.read_csv(output_path)
        assert len(output_df) == 1
        assert output_df['sample_id'].iloc[0] == 'S001'


def test_validate_and_filter_metrics_no_exclusions():
    """Test workflow when no samples are excluded."""
    data = {
        'sample_id': ['S001', 'S002'],
        'PCE': [15.2, 18.5],
        'J_sc': [22.1, 23.5],
        'V_oc': [1.05, 1.10]
    }
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / 'input.csv'
        output_path = Path(tmpdir) / 'output.csv'

        df.to_csv(input_path, index=False)

        stats = validate_and_filter_metrics(
            str(input_path),
            str(output_path)
        )

        assert stats['total_samples'] == 2
        assert stats['valid_samples'] == 2
        assert stats['excluded_count'] == 0


def test_log_warnings_for_excluded_samples(sample_dataframe, caplog):
    """Test that warnings are logged for each excluded sample."""
    caplog.set_level(logging.WARNING)

    identify_missing_metrics(sample_dataframe)

    # Check that warnings were logged for each missing sample
    warning_messages = [record.message for record in caplog.records
                      if record.levelno == logging.WARNING]

    assert len(warning_messages) == 3
    assert any('S002' in msg for msg in warning_messages)
    assert any('S003' in msg for msg in warning_messages)
    assert any('S004' in msg for msg in warning_messages)