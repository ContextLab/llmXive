import os
import sys
import json
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import io

# Add code to path
sys.path.insert(0, 'code')
from download import validate_dataset, fetch_physionet_metadata, main

@pytest.fixture
def valid_metadata_df():
    data = {
        'participant_id': ['P01', 'P02', 'P03', 'P04'],
        'pre_fatigue': [1.0, 2.0, 3.0, 4.0],
        'post_fatigue': [5.0, 6.0, 7.0, 8.0],
        'age': [20, 21, 22, 23]
    }
    return pd.DataFrame(data)

@pytest.fixture
def missing_pair_metadata_df():
    data = {
        'participant_id': ['P01', 'P02'],
        'age': [20, 21],
        'other_col': ['a', 'b']
    }
    return pd.DataFrame(data)

@pytest.fixture
def partial_missing_values_df():
    data = {
        'participant_id': ['P01', 'P02', 'P03'],
        'pre_fatigue': [1.0, None, 3.0],
        'post_fatigue': [5.0, 6.0, 'N/A']
    }
    return pd.DataFrame(data)

def test_validate_dataset_success(valid_metadata_df, caplog):
    is_valid, variables_found, structural_fail, missing_participants = validate_dataset(valid_metadata_df, caplog)
    assert is_valid is True
    assert structural_fail is False
    assert 'pre_fatigue' in variables_found
    assert 'post_fatigue' in variables_found
    assert len(missing_participants) == 0

def test_validate_dataset_structural_failure(missing_pair_metadata_df, caplog):
    is_valid, variables_found, structural_fail, missing_participants = validate_dataset(missing_pair_metadata_df, caplog)
    assert is_valid is False
    assert structural_fail is True
    assert len(missing_participants) == 0

def test_validate_dataset_partial_exclusion(partial_missing_values_df, caplog):
    is_valid, variables_found, structural_fail, missing_participants = validate_dataset(partial_missing_values_df, caplog)
    assert is_valid is True
    assert structural_fail is False
    assert len(missing_participants) == 2 # P02 and P03 have missing values
    assert missing_participants[0]['participant_id'] == 'P02'
    assert missing_participants[1]['participant_id'] == 'P03'

@patch('download.requests.head')
@patch('download.requests.get')
def test_fetch_physionet_metadata_success(mock_get, mock_head, valid_metadata_df, caplog):
    mock_head.return_value.status_code = 200
    mock_get.return_value.status_code = 200
    mock_get.return_value.headers = {'Content-Type': 'text/csv'}
    mock_get.return_value.text = valid_metadata_df.to_csv(index=False)
    
    df = fetch_physionet_metadata("http://example.com/metadata.csv", caplog)
    assert df is not None
    assert len(df) == 4

@patch('download.requests.head')
@patch('download.requests.get')
def test_fetch_physionet_metadata_failure(mock_get, mock_head, caplog):
    mock_head.return_value.status_code = 404
    
    df = fetch_physionet_metadata("http://example.com/missing.csv", caplog)
    assert df is None
