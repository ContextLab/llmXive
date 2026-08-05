import pytest
import os
import sys
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import io

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download import load_config, setup_logger, write_validation_report, fetch_physionet_metadata, validate_dataset, main

def test_validate_dataset_structural_failure():
    """Test that validation fails when required columns are missing."""
    # Create a mock dataframe without the required columns
    df = pd.DataFrame({
        'subject': ['01', '02'],
        'other_col': ['a', 'b']
    })
    
    logger = setup_logger()
    is_valid, found, missing, available = validate_dataset(df, logger)
    
    assert is_valid is False
    assert len(found) == 0
    assert len(missing) == 2
    assert 'pre_fatigue (or variation)' in missing
    assert 'post_fatigue (or variation)' in missing

def test_validate_dataset_structural_success():
    """Test that validation passes when required columns are present."""
    # Create a mock dataframe with required columns
    df = pd.DataFrame({
        'subject': ['01', '02'],
        'pre_fatigue': [1.0, 2.0],
        'post_fatigue': [3.0, 4.0]
    })
    
    logger = setup_logger()
    is_valid, found, missing, available = validate_dataset(df, logger)
    
    assert is_valid is True
    assert len(found) == 2
    assert 'pre_fatigue' in found
    assert 'post_fatigue' in found

def test_validate_dataset_participant_exclusion():
    """Test that participants with missing ratings are identified."""
    # Create a mock dataframe with some missing ratings
    df = pd.DataFrame({
        'subject': ['01', '02', '03'],
        'pre_fatigue': [1.0, None, 3.0],
        'post_fatigue': [2.0, 4.0, None]
    })
    
    logger = setup_logger()
    is_valid, found, missing, available = validate_dataset(df, logger)
    
    # Structure is valid (columns exist)
    assert is_valid is True
    assert len(found) == 2

@patch('download.requests.head')
@patch('download.requests.get')
def test_fetch_physionet_metadata(mock_get, mock_head):
    """Test fetching metadata from PhysioNet."""
    # Mock HEAD request
    mock_head.return_value.status_code = 200
    
    # Mock GET request to return a CSV string
    csv_content = "subject,pre_fatigue,post_fatigue\n01,1.0,2.0\n02,3.0,4.0"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = csv_content
    mock_get.return_value = mock_response
    
    logger = setup_logger()
    df = fetch_physionet_metadata("https://example.com", logger)
    
    assert df is not None
    assert len(df) == 2
    assert 'subject' in df.columns
    assert 'pre_fatigue' in df.columns

@patch('download.requests.head')
@patch('download.requests.get')
def test_fetch_physionet_metadata_failure(mock_get, mock_head):
    """Test fetching metadata when the request fails."""
    # Mock HEAD request to fail
    mock_head.return_value.status_code = 404
    
    logger = setup_logger()
    df = fetch_physionet_metadata("https://example.com", logger)
    
    assert df is None

def test_write_validation_report():
    """Test writing a validation report."""
    report_path = write_validation_report("error", "Test error", {"key": "value"})
    
    assert os.path.exists(report_path)
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report['status'] == 'error'
    assert report['message'] == 'Test error'
    assert report['details']['key'] == 'value'

def test_main_structural_failure():
    """Test that main exits with code 1 when validation fails."""
    # Mock the functions to simulate a structural failure
    with patch('download.fetch_physionet_metadata') as mock_fetch, \
         patch('download.validate_dataset') as mock_validate, \
         patch('download.sys.exit') as mock_exit, \
         patch('download.write_validation_report') as mock_report:
        
        mock_fetch.return_value = pd.DataFrame({'subject': ['01']})
        mock_validate.return_value = (False, [], ['pre_fatigue'], ['subject'])
        
        main()
        
        mock_exit.assert_called_once_with(1)
        mock_report.assert_called_once()

def test_main_success():
    """Test that main exits with code 0 when validation succeeds."""
    # Mock the functions to simulate a successful validation
    with patch('download.fetch_physionet_metadata') as mock_fetch, \
         patch('download.validate_dataset') as mock_validate, \
         patch('download.download_raw_data') as mock_download, \
         patch('download.sys.exit') as mock_exit, \
         patch('download.write_validation_report') as mock_report:
        
        mock_fetch.return_value = pd.DataFrame({'subject': ['01'], 'pre_fatigue': [1.0], 'post_fatigue': [2.0]})
        mock_validate.return_value = (True, ['pre_fatigue', 'post_fatigue'], [], ['subject', 'pre_fatigue', 'post_fatigue'])
        mock_download.return_value = True
        
        main()
        
        mock_exit.assert_called_once_with(0)
        mock_report.assert_not_called()
