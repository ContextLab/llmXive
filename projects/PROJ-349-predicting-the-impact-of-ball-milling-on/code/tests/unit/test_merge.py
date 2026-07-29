"""
Unit tests for the merge module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from src.ingest.merge import calculate_row_hash, merge_datasets, validate_traceability, run_merge_pipeline
from src.exceptions import DataIngestionError


@pytest.fixture
def sample_df_1():
    return pd.DataFrame({
        'experiment_id': ['exp1', 'exp2'],
        'source_name': ['Materials Project', 'Materials Project'],
        'source_id': ['mp-1', 'mp-2'],
        'd50': [10.5, 20.3]
    })


@pytest.fixture
def sample_df_2():
    return pd.DataFrame({
        'experiment_id': ['exp3', 'exp4'],
        'source_name': ['NIST', 'arXiv'],
        'source_id': ['nist-1', 'arxiv-1'],
        'd50': [15.2, 25.1]
    })


@pytest.fixture
def empty_df():
    return pd.DataFrame()


@pytest.fixture
def mock_fallback_data():
    return [
        {'experiment_id': 'exp1', 'image_path': '/fake/path.png', 'issue_type': 'missing_d50'}
    ]


def test_calculate_row_hash():
    """Test that identical rows produce the same hash."""
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    hash1 = calculate_row_hash(df.iloc[0])
    hash2 = calculate_row_hash(df.iloc[0])
    assert hash1 == hash2

    hash3 = calculate_row_hash(df.iloc[1])
    assert hash1 != hash3


def test_merge_datasets_no_duplicates(sample_df_1, sample_df_2):
    """Test merging two dataframes with no duplicates."""
    result = merge_datasets([sample_df_1, sample_df_2])
    assert len(result) == 4
    assert set(result['experiment_id']) == {'exp1', 'exp2', 'exp3', 'exp4'}


def test_merge_datasets_with_duplicates(sample_df_1):
    """Test merging dataframes that contain duplicate rows."""
    # Create a duplicate of the first row
    duplicate_df = sample_df_1.copy()
    result = merge_datasets([sample_df_1, duplicate_df])
    assert len(result) == 2  # Duplicates should be removed


def test_merge_datasets_empty_list():
    """Test merging an empty list of dataframes."""
    result = merge_datasets([])
    assert result.empty


def test_merge_datasets_all_empty():
    """Test merging dataframes that are all empty."""
    df1 = pd.DataFrame()
    df2 = pd.DataFrame()
    result = merge_datasets([df1, df2])
    assert result.empty


def test_validate_traceability_valid(sample_df_1):
    """Test validation with valid data (no missing traceability)."""
    filtered_df, count = validate_traceability(sample_df_1)
    assert count == 0
    assert len(filtered_df) == len(sample_df_1)


def test_validate_traceability_missing_source(sample_df_1):
    """Test validation with missing source_name."""
    df = sample_df_1.copy()
    df.loc[0, 'source_name'] = None
    filtered_df, count = validate_traceability(df)
    assert count == 1
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['experiment_id'] == 'exp2'


def test_validate_traceability_missing_id(sample_df_1):
    """Test validation with missing source_id."""
    df = sample_df_1.copy()
    df.loc[1, 'source_id'] = None
    filtered_df, count = validate_traceability(df)
    assert count == 1
    assert len(filtered_df) == 1


def test_validate_traceability_empty():
    """Test validation on an empty dataframe."""
    df = pd.DataFrame()
    filtered_df, count = validate_traceability(df)
    assert filtered_df.empty
    assert count == 0


@patch('src.ingest.merge.load_config')
@patch('src.ingest.merge.extract_psd_from_image')
@patch('builtins.open', new_callable=MagicMock)
def test_run_merge_pipeline_with_fallback(
    mock_open_file,
    mock_extract,
    mock_load_config,
    sample_df_1,
    mock_fallback_data
):
    """Test the full merge pipeline with OCR fallback."""
    # Mock config
    mock_load_config.return_value = {'ocr_enabled': True}

    # Mock file read for flagged entries
    mock_open_file.return_value.__enter__.return_value.read.return_value = (
        '{"experiment_id": "exp1", "image_path": "/fake/path.png", "issue_type": "missing_d50"}'
    )

    # Mock extraction result
    mock_extract.return_value = {'d50': 12.5}

    # Mock parquet write
    with patch('pyarrow.parquet.write_table'):
        result = run_merge_pipeline(materials_df=sample_df_1)

    # Verify extraction was called
    mock_extract.assert_called_once()
    # Verify the d50 was updated for exp1
    assert result.loc[result['experiment_id'] == 'exp1', 'd50'].iloc[0] == 12.5


@patch('src.ingest.merge.load_config')
def test_run_merge_pipeline_no_fallback_needed(mock_load_config, sample_df_1):
    """Test merge pipeline when no flagged entries exist."""
    mock_load_config.return_value = {'ocr_enabled': True}

    with patch('pathlib.Path.exists', return_value=False):
        with patch('pyarrow.parquet.write_table'):
            result = run_merge_pipeline(materials_df=sample_df_1)

    assert len(result) == 2


@patch('src.ingest.merge.load_config')
def test_run_merge_pipeline_fallback_unavailable(mock_load_config, sample_df_1):
    """Test merge pipeline when OCR is disabled."""
    mock_load_config.return_value = {'ocr_enabled': False}

    with patch('pathlib.Path.exists', return_value=True):
        with patch('builtins.open', new_callable=MagicMock):
            with patch('pyarrow.parquet.write_table'):
                result = run_merge_pipeline(materials_df=sample_df_1)

    assert len(result) == 2