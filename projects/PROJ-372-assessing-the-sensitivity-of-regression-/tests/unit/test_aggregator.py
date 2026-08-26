"""
Unit tests for the aggregator module.
"""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.resampling.aggregator import (
    calculate_empirical_sd,
    load_resampling_results,
    run_aggregation_pipeline
)


@pytest.fixture
def sample_results():
    """Create sample resampling results for testing."""
    return [
        {
            'tier': 10,
            'subset_id': 'sub_001',
            'coefficients': {'intercept': 1.0, 'x1': 2.0, 'x2': 3.0},
            'valid': True
        },
        {
            'tier': 10,
            'subset_id': 'sub_002',
            'coefficients': {'intercept': 1.1, 'x1': 2.1, 'x2': 3.1},
            'valid': True
        },
        {
            'tier': 10,
            'subset_id': 'sub_003',
            'coefficients': {'intercept': 0.9, 'x1': 1.9, 'x2': 2.9},
            'valid': True
        },
        {
            'tier': 25,
            'subset_id': 'sub_004',
            'coefficients': {'intercept': 1.05, 'x1': 2.05, 'x2': 3.05},
            'valid': True
        },
        {
            'tier': 25,
            'subset_id': 'sub_005',
            'coefficients': {'intercept': 0.95, 'x1': 1.95, 'x2': 2.95},
            'valid': True
        },
        {
            'tier': 10,
            'subset_id': 'sub_006',
            'coefficients': {'intercept': 1.0, 'x1': 2.0, 'x2': 3.0},
            'valid': False  # Invalid result should be excluded
        }
    ]


def test_calculate_empirical_sd_basic(sample_results):
    """Test basic calculation of empirical standard deviation."""
    result_df = calculate_empirical_sd(sample_results)

    assert isinstance(result_df, pd.DataFrame)
    assert 'tier' in result_df.columns
    assert 'feature' in result_df.columns
    assert 'mean_coefficient' in result_df.columns
    assert 'std_coefficient' in result_df.columns
    assert 'n_valid' in result_df.columns

    # Check that we have results for both tiers
    tiers = sorted(result_df['tier'].unique())
    assert tiers == [10, 25]

    # Check that std is positive
    assert (result_df['std_coefficient'] > 0).all()


def test_calculate_empirical_sd_empty_results():
    """Test handling of empty results list."""
    result_df = calculate_empirical_sd([])

    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == 0
    assert list(result_df.columns) == ['tier', 'feature', 'mean_coefficient', 'std_coefficient', 'n_valid']


def test_calculate_empirical_sd_no_valid_results():
    """Test handling when no valid results exist."""
    results = [
        {'tier': 10, 'subset_id': 'sub_001', 'coefficients': {'x1': 1.0}, 'valid': False},
        {'tier': 10, 'subset_id': 'sub_002', 'coefficients': {'x1': 2.0}, 'valid': False}
    ]
    result_df = calculate_empirical_sd(results)

    assert len(result_df) == 0


def test_calculate_empirical_sd_output_file(sample_results):
    """Test that output file is created correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_output.csv')
        result_df = calculate_empirical_sd(sample_results, output_path=output_path)

        assert os.path.exists(output_path)

        # Verify file content
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == len(result_df)
        assert list(saved_df.columns) == list(result_df.columns)


def test_load_resampling_results(tmp_path):
    """Test loading results from JSON files."""
    # Create test data
    results_data = [
        {'tier': 10, 'subset_id': 'sub_001', 'coefficients': {'x1': 1.0}, 'valid': True},
        {'tier': 10, 'subset_id': 'sub_002', 'coefficients': {'x1': 2.0}, 'valid': True}
    ]

    # Write to file
    test_file = tmp_path / "results.json"
    with open(test_file, 'w') as f:
        json.dump(results_data, f)

    # Load and verify
    loaded = load_resampling_results(str(tmp_path))
    assert len(loaded) == 2
    assert loaded[0]['tier'] == 10
    assert loaded[0]['valid'] is True


def test_load_resampling_results_empty_directory(tmp_path):
    """Test loading from empty directory."""
    loaded = load_resampling_results(str(tmp_path))
    assert len(loaded) == 0


def test_run_aggregation_pipeline(tmp_path):
    """Test full aggregation pipeline."""
    # Create test data
    results_data = [
        {'tier': 10, 'subset_id': 'sub_001', 'coefficients': {'x1': 1.0, 'x2': 2.0}, 'valid': True},
        {'tier': 10, 'subset_id': 'sub_002', 'coefficients': {'x1': 1.5, 'x2': 2.5}, 'valid': True},
        {'tier': 25, 'subset_id': 'sub_003', 'coefficients': {'x1': 1.2, 'x2': 2.2}, 'valid': True}
    ]

    # Write to file
    results_file = tmp_path / "results.json"
    with open(results_file, 'w') as f:
        json.dump(results_data, f)

    # Define output paths
    csv_output = tmp_path / "aggregated.csv"
    json_output = tmp_path / "aggregated.json"

    # Run pipeline
    result_df = run_aggregation_pipeline(
        results_dir=str(tmp_path),
        output_csv=str(csv_output),
        output_json=str(json_output)
    )

    # Verify outputs exist
    assert csv_output.exists()
    assert json_output.exists()

    # Verify content
    saved_csv = pd.read_csv(csv_output)
    assert len(saved_csv) == len(result_df)

    # Check that we have results for both tiers
    assert 10 in saved_csv['tier'].values
    assert 25 in saved_csv['tier'].values


def test_calculate_empirical_sd_nan_handling(sample_results):
    """Test that NaN values are excluded from calculation."""
    # Add a result with NaN
    results_with_nan = sample_results + [
        {
            'tier': 10,
            'subset_id': 'sub_007',
            'coefficients': {'intercept': np.nan, 'x1': 2.0, 'x2': 3.0},
            'valid': True
        }
    ]

    result_df = calculate_empirical_sd(results_with_nan)

    # Should still calculate valid results (NaN should be excluded)
    assert len(result_df) > 0
    assert not result_df['std_coefficient'].isna().any()
