"""
Tests for the main pipeline orchestration (T021).

Verifies:
1. Directory structure creation
2. Raw data checksum generation
3. Processed data saving
4. Schema validation enforcement
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

import pytest
from unittest.mock import patch, MagicMock, mock_open

from main import main, ensure_directories
from setup_data_directories import setup_data_directories
from utils.hashing import load_checksums, compute_file_hash
from exceptions import ConfigurationError

@pytest.fixture
def temp_project_root():
    """Create a temporary project directory structure."""
    temp_dir = tempfile.mkdtemp()
    root = Path(temp_dir) / "projects" / "PROJ-064-statistical-discrepancies-in-publicly-av"
    root.mkdir(parents=True)
    yield root
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_csv_data():
    """Generate sample CSV data for testing ingestion."""
    data = {
        'jurisdiction_id': ['J1', 'J2', 'J3'],
        'precinct_votes': [100, 200, 150],
        'county_reported': [105, 195, 160],
        'year': [2020, 2020, 2020]
    }
    return pd.DataFrame(data)

def test_ensure_directories(temp_project_root):
    """Test that ensure_directories creates the required folder structure."""
    ensure_directories(temp_project_root)
    
    required_dirs = [
        'data/raw',
        'data/processed',
        'state',
        'logs',
        'config'
    ]
    
    for dir_name in required_dirs:
        full_path = temp_project_root / dir_name
        assert full_path.exists(), f"Directory {full_path} was not created"
        assert full_path.is_dir(), f"{full_path} is not a directory"

@patch('main.DataIngestionPipeline')
@patch('main.DiscrepancyCalculator')
@patch('main.setup_logging')
@patch('main.get_logger')
def test_main_saves_raw_with_checksum(
    mock_get_logger, 
    mock_setup_logging, 
    mock_calculator, 
    mock_ingestion,
    temp_project_root,
    sample_csv_data
):
    """
    Test that main() saves raw data to data/raw/ with a checksum in state/.
    """
    # Setup mocks
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    
    # Mock ingestion to return a fake raw file path
    raw_file = temp_project_root / "data" / "raw" / "test_raw.csv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    sample_csv_data.to_csv(raw_file, index=False)
    
    mock_ingestion_instance = MagicMock()
    mock_ingestion_instance.run.return_value = raw_file
    mock_ingestion.return_value = mock_ingestion_instance

    # Mock calculator to return processed data
    processed_df = sample_csv_data.copy()
    processed_df['discrepancy_abs'] = 5
    processed_df['discrepancy_pct'] = 0.05
    processed_df['missing_data'] = False
    
    mock_calc_instance = MagicMock()
    mock_calc_instance.process.return_value = processed_df
    mock_calculator.return_value = mock_calc_instance

    # Mock sys.argv
    test_args = [
        'main.py',
        '--project-root', str(temp_project_root),
        '--output-format', 'csv'
    ]
    
    with patch.object(sys, 'argv', test_args):
        result = main()
    
    assert result == 0
    
    # Verify raw checksum exists
    checksum_file = temp_project_root / "state" / "raw_data_checksum.json"
    assert checksum_file.exists(), "Raw data checksum file was not created"
    
    with open(checksum_file, 'r') as f:
        checksums = json.load(f)
    
    assert 'test_raw.csv' in checksums, "Raw file name not in checksums"
    assert checksums['test_raw.csv'] == compute_file_hash(raw_file), "Checksum mismatch"

@patch('main.DataIngestionPipeline')
@patch('main.DiscrepancyCalculator')
@patch('main.setup_logging')
@patch('main.get_logger')
def test_main_saves_processed_data(
    mock_get_logger, 
    mock_setup_logging, 
    mock_calculator, 
    mock_ingestion,
    temp_project_root,
    sample_csv_data
):
    """
    Test that main() saves processed data to data/processed/.
    """
    # Setup mocks
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    
    raw_file = temp_project_root / "data" / "raw" / "test_raw.csv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    sample_csv_data.to_csv(raw_file, index=False)
    
    mock_ingestion_instance = MagicMock()
    mock_ingestion_instance.run.return_value = raw_file
    mock_ingestion.return_value = mock_ingestion_instance

    processed_df = sample_csv_data.copy()
    processed_df['discrepancy_abs'] = 5
    processed_df['discrepancy_pct'] = 0.05
    processed_df['missing_data'] = False
    
    mock_calc_instance = MagicMock()
    mock_calc_instance.process.return_value = processed_df
    mock_calculator.return_value = mock_calc_instance

    test_args = [
        'main.py',
        '--project-root', str(temp_project_root),
        '--output-format', 'csv'
    ]
    
    with patch.object(sys, 'argv', test_args):
        result = main()
    
    assert result == 0
    
    processed_file = temp_project_root / "data" / "processed" / "discrepancies_processed.csv"
    assert processed_file.exists(), "Processed data file was not created"
    
    # Verify content
    saved_df = pd.read_csv(processed_file)
    assert list(saved_df.columns) == list(processed_df.columns)
    assert len(saved_df) == len(processed_df)

@patch('main.DataIngestionPipeline')
@patch('main.DiscrepancyCalculator')
@patch('main.setup_logging')
@patch('main.get_logger')
@patch('main.validate_output_schema')
def test_main_fails_on_invalid_schema(
    mock_validate_schema,
    mock_get_logger, 
    mock_setup_logging, 
    mock_calculator, 
    mock_ingestion,
    temp_project_root,
    sample_csv_data
):
    """
    Test that main() raises ConfigurationError if output schema is invalid.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    
    raw_file = temp_project_root / "data" / "raw" / "test_raw.csv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    sample_csv_data.to_csv(raw_file, index=False)
    
    mock_ingestion_instance = MagicMock()
    mock_ingestion_instance.run.return_value = raw_file
    mock_ingestion.return_value = mock_ingestion_instance

    mock_calc_instance = MagicMock()
    mock_calc_instance.process.return_value = sample_csv_data # Invalid schema (missing discrepancy cols)
    mock_calculator.return_value = mock_calc_instance

    mock_validate_schema.return_value = False

    test_args = [
        'main.py',
        '--project-root', str(temp_project_root),
        '--output-format', 'csv'
    ]
    
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(ConfigurationError, match="Processed data does not match required schema"):
            main()
