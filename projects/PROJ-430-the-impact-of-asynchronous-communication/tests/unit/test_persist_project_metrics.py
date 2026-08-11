"""
Unit tests for T015: persist_project_metrics.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the functions to test
from persist_project_metrics import (
    load_pair_metrics,
    aggregate_to_project_level,
    run_aggregation_pipeline
)
from config import get_config


@pytest.fixture
def sample_pair_data():
    """
    Create a small in-memory DataFrame mimicking the parquet input.
    Structure: project_id, pair_id, response_time_variance, mean_delay
    """
    data = {
        'project_id': ['P1', 'P1', 'P1', 'P2', 'P2'],
        'pair_id': ['A', 'B', 'C', 'D', 'E'],
        'response_time_variance': [10.0, 20.0, 30.0, 5.0, 15.0],
        'mean_delay': [100.0, 200.0, 300.0, 50.0, 150.0]
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_parquet_file(sample_pair_data):
    """
    Creates a temporary parquet file with sample data for testing load_pair_metrics.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / 'test_timestamp_features.parquet'
        sample_pair_data.to_parquet(path)
        yield path


@pytest.fixture
def temp_output_dir():
    """
    Creates a temporary directory for output files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_load_pair_metrics(temp_parquet_file, sample_pair_data):
    """Test that load_pair_metrics correctly reads the parquet file."""
    result = load_pair_metrics(temp_parquet_file)
    assert len(result) == len(sample_pair_data)
    assert set(result.columns) == {'project_id', 'pair_id', 'response_time_variance', 'mean_delay'}
    # Check specific values
    assert result.loc[0, 'project_id'] == 'P1'
    assert result.loc[0, 'response_time_variance'] == 10.0


def test_load_pair_metrics_missing_file():
    """Test that load_pair_metrics raises FileNotFoundError for missing input."""
    with pytest.raises(FileNotFoundError):
        load_pair_metrics(Path('/nonexistent/path/file.parquet'))


def test_load_pair_metrics_missing_columns(temp_parquet_file, sample_pair_data):
    """Test that load_pair_metrics raises ValueError if columns are missing."""
    # Create a file with missing columns
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        bad_data = sample_pair_data.drop(columns=['response_time_variance'])
        bad_data.to_parquet(f.name)
        bad_path = Path(f.name)

    with pytest.raises(ValueError) as excinfo:
        load_pair_metrics(bad_path)
    assert "Missing required columns" in str(excinfo.value)
    os.unlink(bad_path)


def test_aggregate_to_project_level(sample_pair_data):
    """
    Test the aggregation logic.
    P1: variances [10, 20, 30] -> median = 20.0
    P1: delays [100, 200, 300] -> mean = 200.0
    P2: variances [5, 15] -> median = 10.0
    P2: delays [50, 150] -> mean = 100.0
    """
    result = aggregate_to_project_level(sample_pair_data)

    assert len(result) == 2
    assert set(result['project_id']) == {'P1', 'P2'}

    p1_row = result[result['project_id'] == 'P1'].iloc[0]
    assert p1_row['median_variance'] == 20.0
    assert p1_row['mean_delay'] == 200.0
    assert p1_row['pair_count'] == 3

    p2_row = result[result['project_id'] == 'P2'].iloc[0]
    assert p2_row['median_variance'] == 10.0
    assert p2_row['mean_delay'] == 100.0
    assert p2_row['pair_count'] == 2


def test_aggregate_to_project_level_empty_df():
    """Test aggregation with an empty dataframe."""
    empty_df = pd.DataFrame(columns=['project_id', 'pair_id', 'response_time_variance', 'mean_delay'])
    result = aggregate_to_project_level(empty_df)
    assert len(result) == 0
    assert 'median_variance' in result.columns


def test_run_aggregation_pipeline(temp_parquet_file, temp_output_dir, sample_pair_data):
    """
    Test the full pipeline: load -> aggregate -> save.
    """
    output_file = temp_output_dir / 'project_metrics.csv'

    # Mock config to use temp dir? No, we pass paths directly to the function if possible,
    # but run_aggregation_pipeline doesn't take output_path in the signature used in the test
    # Wait, the function signature is: run_aggregation_pipeline(input_path, output_path)
    # So we can pass them.
    
    result_path = run_aggregation_pipeline(
        input_path=temp_parquet_file,
        output_path=output_file
    )

    assert result_path == output_file
    assert result_path.exists()

    # Verify content
    saved_df = pd.read_csv(result_path)
    assert len(saved_df) == 2
    assert 'median_variance' in saved_df.columns
    assert 'mean_delay' in saved_df.columns
    assert 'pair_count' in saved_df.columns
    
    # Verify values match expectations from test_aggregate_to_project_level
    p1_row = saved_df[saved_df['project_id'] == 'P1'].iloc[0]
    assert p1_row['median_variance'] == 20.0
    assert p1_row['mean_delay'] == 200.0