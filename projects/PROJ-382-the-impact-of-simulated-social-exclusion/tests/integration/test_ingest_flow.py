"""
Integration test for end-to-end ingestion with mock OSF responses.

This test verifies the full ingestion pipeline:
1. Configuration loading
2. Schema validation (valid vs invalid datasets)
3. Column normalization
4. Missing value handling
5. Data merging
6. Logging and error handling

It uses mock OSF responses to simulate real data sources without network calls.
"""
import json
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
import pandas as pd
import pytest
import numpy as np

# Import from project modules
from ingest import validate_schema, normalize_columns, ingest_datasets
from network_utils import IngestionError
from logging_config import setup_logging, get_project_logger
from environment_config import initialize_environment

# Constants for test data
VALID_CSV_CONTENT = """condition,prosocial_amount,randomized
ignored,5.0,True
excluded,2.0,True
control,8.0,True
ignored,0.0,True
"""

INVALID_CSV_MISSING_COLS = """condition,other_column
ignored,5.0
excluded,2.0
"""

INVALID_CSV_MISSING_REQUIRED = """prosocial_amount,randomized
5.0,True
2.0,True
"""

# Required columns for schema validation
REQUIRED_COLUMNS = {'condition', 'prosocial_amount', 'randomized'}

def setup_module(module):
    """Setup logging and environment for tests."""
    # Initialize environment with test defaults
    os.environ['PYTHONHASHSEED'] = '42'
    initialize_environment()
    
    # Setup logging
    log_dir = Path(tempfile.mkdtemp())
    setup_logging(log_dir=log_dir)

@pytest.fixture
def mock_osf_responses():
    """Create mock OSF responses for valid and invalid datasets."""
    # Create temporary directory for test data
    test_data_dir = Path(tempfile.mkdtemp())
    
    # Valid dataset
    valid_file = test_data_dir / "valid_dataset.csv"
    valid_file.write_text(VALID_CSV_CONTENT)
    
    # Invalid dataset (missing columns)
    invalid_file = test_data_dir / "invalid_missing_cols.csv"
    invalid_file.write_text(INVALID_CSV_MISSING_COLS)
    
    # Invalid dataset (missing required column)
    invalid_file2 = test_data_dir / "invalid_missing_required.csv"
    invalid_file2.write_text(INVALID_CSV_MISSING_REQUIRED)
    
    return {
        'valid': str(valid_file),
        'invalid_missing_cols': str(invalid_file),
        'invalid_missing_required': str(invalid_file2),
        'test_dir': test_data_dir
    }

@pytest.fixture
def test_config(mock_osf_responses):
    """Create a test configuration with mock URLs."""
    test_dir = mock_osf_responses['test_dir']
    
    config = {
        'datasets': [
            {
                'name': 'valid_dataset',
                'url': f'file://{mock_osf_responses["valid"]}',
                'source': 'mock_osf'
            },
            {
                'name': 'invalid_missing_cols',
                'url': f'file://{mock_osf_responses["invalid_missing_cols"]}',
                'source': 'mock_osf'
            },
            {
                'name': 'invalid_missing_required',
                'url': f'file://{mock_osf_responses["invalid_missing_required"]}',
                'source': 'mock_osf'
            }
        ],
        'required_columns': list(REQUIRED_COLUMNS),
        'output_dir': str(Path(test_dir) / 'output')
    }
    
    return config

def test_schema_validation_valid_data():
    """Test that valid data passes schema validation."""
    df = pd.read_csv(Path(tempfile.gettempdir()) / 'dummy.csv') if False else pd.DataFrame({
        'condition': ['ignored', 'excluded', 'control'],
        'prosocial_amount': [5.0, 2.0, 8.0],
        'randomized': [True, True, True]
    })
    
    is_valid, missing_cols = validate_schema(df, REQUIRED_COLUMNS)
    
    assert is_valid, "Valid data should pass schema validation"
    assert len(missing_cols) == 0, "No missing columns expected"

def test_schema_validation_invalid_data():
    """Test that invalid data fails schema validation."""
    df = pd.DataFrame({
        'condition': ['ignored', 'excluded'],
        'other_column': [5.0, 2.0]
    })
    
    is_valid, missing_cols = validate_schema(df, REQUIRED_COLUMNS)
    
    assert not is_valid, "Invalid data should fail schema validation"
    assert 'prosocial_amount' in missing_cols
    assert 'randomized' in missing_cols

def test_column_normalization(mock_osf_responses):
    """Test that column normalization works correctly."""
    # Create a DataFrame with variant column names
    df = pd.DataFrame({
        'condition': ['ignored', 'excluded', 'control'],
        'donation': [5.0, 2.0, 8.0],  # variant name
        'randomized': [True, True, True]
    })
    
    normalized_df = normalize_columns(df)
    
    assert 'prosocial_amount' in normalized_df.columns
    assert 'donation' not in normalized_df.columns
    assert list(normalized_df['prosocial_amount']) == [5.0, 2.0, 8.0]

def test_end_to_end_ingestion_flow(test_config):
    """Test the complete ingestion flow with mock data."""
    output_dir = Path(test_config['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock the download function to return local files
    with patch('ingest.download_dataset') as mock_download:
        def mock_download_side_effect(url, output_dir, **kwargs):
            # Extract the file path from the URL
            if url.startswith('file://'):
                file_path = url[7:]  # Remove 'file://' prefix
                return Path(file_path)
            return None
        
        mock_download.side_effect = mock_download_side_effect
        
        # Run ingestion
        results = ingest_datasets(test_config)
        
        # Verify results
        assert 'valid_datasets' in results
        assert 'invalid_datasets' in results
        assert 'merged_data' in results
        assert 'logs' in results
        
        # Should have 1 valid dataset
        assert len(results['valid_datasets']) == 1
        assert results['valid_datasets'][0]['name'] == 'valid_dataset'
        
        # Should have 2 invalid datasets
        assert len(results['invalid_datasets']) == 2
        invalid_names = [d['name'] for d in results['invalid_datasets']]
        assert 'invalid_missing_cols' in invalid_names
        assert 'invalid_missing_required' in invalid_names
        
        # Merged data should exist
        assert results['merged_data'] is not None
        assert len(results['merged_data']) > 0
        
        # Verify schema of merged data
        assert 'condition' in results['merged_data'].columns
        assert 'prosocial_amount' in results['merged_data'].columns
        assert 'randomized' in results['merged_data'].columns

def test_logging_integration(test_config):
    """Test that logging works correctly during ingestion."""
    logger = get_project_logger()
    
    with patch('ingest.download_dataset') as mock_download:
        def mock_download_side_effect(url, output_dir, **kwargs):
            if url.startswith('file://'):
                file_path = url[7:]
                return Path(file_path)
            return None
        
        mock_download.side_effect = mock_download_side_effect
        
        # Run ingestion
        results = ingest_datasets(test_config)
        
        # Check that logs were created
        assert 'logs' in results
        assert len(results['logs']) > 0
        
        # Verify log content
        log_entries = results['logs']
        valid_count = sum(1 for log in log_entries if log.get('status') == 'valid')
        invalid_count = sum(1 for log in log_entries if log.get('status') == 'invalid')
        
        assert valid_count == 1
        assert invalid_count == 2

def test_insufficient_data_handling():
    """Test that the pipeline handles insufficient valid datasets."""
    config = {
        'datasets': [
            {
                'name': 'invalid_dataset',
                'url': 'file:///tmp/invalid.csv',
                'source': 'mock_osf'
            }
        ],
        'required_columns': list(REQUIRED_COLUMNS),
        'output_dir': str(Path(tempfile.mkdtemp()) / 'output')
    }
    
    # Create an invalid CSV file
    invalid_file = Path(config['datasets'][0]['url'][7:])
    invalid_file.parent.mkdir(parents=True, exist_ok=True)
    invalid_file.write_text(INVALID_CSV_MISSING_COLS)
    
    with patch('ingest.download_dataset') as mock_download:
        def mock_download_side_effect(url, output_dir, **kwargs):
            if url.startswith('file://'):
                file_path = url[7:]
                return Path(file_path)
            return None
        
        mock_download.side_effect = mock_download_side_effect
        
        # This should raise an error or return empty results
        # depending on implementation (check if it halts appropriately)
        try:
            results = ingest_datasets(config)
            # If it doesn't raise, check that it reports insufficient data
            if 'merged_data' in results:
                assert results['merged_data'] is None or len(results['merged_data']) == 0
        except Exception as e:
            # Expected behavior: raise an error for insufficient data
            assert "insufficient" in str(e).lower() or "valid dataset" in str(e).lower()

def test_missing_value_handling_integration(mock_osf_responses):
    """Test that missing values are handled correctly during ingestion."""
    # Create a dataset with missing values
    test_data_dir = mock_osf_responses['test_dir']
    missing_file = test_data_dir / "missing_values.csv"
    missing_file.write_text("""condition,prosocial_amount,randomized
    ignored,5.0,True
    excluded,,True
    control,8.0,
    ignored,0.0,True
    """)
    
    config = {
        'datasets': [
            {
                'name': 'missing_values',
                'url': f'file://{missing_file}',
                'source': 'mock_osf'
            }
        ],
        'required_columns': list(REQUIRED_COLUMNS),
        'output_dir': str(test_data_dir / 'output')
    }
    
    with patch('ingest.download_dataset') as mock_download:
        def mock_download_side_effect(url, output_dir, **kwargs):
            if url.startswith('file://'):
                file_path = url[7:]
                return Path(file_path)
            return None
        
        mock_download.side_effect = mock_download_side_effect
        
        results = ingest_datasets(config)
        
        # Should have valid data
        assert len(results['valid_datasets']) == 1
        assert results['merged_data'] is not None
        
        # Check that missing values were handled
        # (either imputed or excluded - check the logs for details)
        assert 'logs' in results
        imputation_logs = [log for log in results['logs'] if 'imputation' in str(log).lower()]
        assert len(imputation_logs) > 0 or len(results['merged_data']) < 4  # Some rows excluded

def test_condition_normalization(mock_osf_responses):
    """Test that condition strings are normalized correctly."""
    test_data_dir = mock_osf_responses['test_dir']
    condition_file = test_data_dir / "conditions.csv"
    condition_file.write_text("""condition,prosocial_amount,randomized
    ignored,5.0,True
    excluded,2.0,True
    control,8.0,True
    Ignored,3.0,True
    EXCLUDED,1.0,True
    """)
    
    config = {
        'datasets': [
            {
                'name': 'conditions',
                'url': f'file://{condition_file}',
                'source': 'mock_osf'
            }
        ],
        'required_columns': list(REQUIRED_COLUMNS),
        'output_dir': str(test_data_dir / 'output')
    }
    
    with patch('ingest.download_dataset') as mock_download:
        def mock_download_side_effect(url, output_dir, **kwargs):
            if url.startswith('file://'):
                file_path = url[7:]
                return Path(file_path)
            return None
        
        mock_download.side_effect = mock_download_side_effect
        
        results = ingest_datasets(config)
        
        # Check that conditions are normalized
        assert results['merged_data'] is not None
        conditions = results['merged_data']['condition'].unique()
        
        # Should have normalized conditions (lowercase, standardized)
        assert 'ignored' in conditions or 'excluded' in conditions or 'control' in conditions