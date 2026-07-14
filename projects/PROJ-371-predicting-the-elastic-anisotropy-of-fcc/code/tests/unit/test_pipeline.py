"""
Unit tests for the pipeline orchestration script (T015).
"""

import os
import sys
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
import pandas as pd

# Mock the data modules to avoid API calls and heavy dependencies
from src.data import ingest
from src.data import clean
from src.data import features

# Import the main function to test
from src.cli.run_pipeline import main

@pytest.fixture
def mock_config():
    """Mock configuration to avoid file system dependencies."""
    return {
        "paths": {
            "raw": "data/raw",
            "processed": "data/processed",
            "output": "output"
        },
        "seed": 42
    }

@pytest.fixture
def sample_ingest_data():
    """Sample data for ingestion mock."""
    return pd.DataFrame({
        'material_id': ['mp-123', 'mp-134'],
        'C11': [100.0, 200.0],
        'C12': [50.0, 100.0],
        'C44': [30.0, 60.0],
        'formula': ['Cu', 'Al']
    })

@pytest.fixture
def sample_clean_data():
    """Sample data for cleaning mock."""
    return pd.DataFrame({
        'material_id': ['mp-123', 'mp-134'],
        'C11': [100.0, 200.0],
        'C12': [50.0, 100.0],
        'C44': [30.0, 60.0],
        'formula': ['Cu', 'Al'],
        'A1': [0.6, 0.6] # Calculated A1
    })

@pytest.fixture
def sample_feature_data():
    """Sample data for feature mock."""
    return pd.DataFrame({
        'material_id': ['mp-123', 'mp-134'],
        'C11': [100.0, 200.0],
        'C12': [50.0, 100.0],
        'C44': [30.0, 60.0],
        'formula': ['Cu', 'Al'],
        'A1': [0.6, 0.6],
        'radius_variance': [0.0, 0.0],
        'electronegativity_std': [0.0, 0.0],
        'vec': [11.0, 13.0]
    })

def test_pipeline_execution(mock_config, sample_ingest_data, sample_clean_data, sample_feature_data, tmp_path):
    """Test that the pipeline runs end-to-end with mocked dependencies."""
    
    # Setup temporary output directory
    output_dir = tmp_path / "data" / "processed"
    output_dir.mkdir(parents=True)
    output_file = output_dir / "elastic_anisotropy.csv"

    # Patch dependencies
    with patch('src.cli.run_pipeline.get_config', return_value=mock_config), \
         patch('src.cli.run_pipeline.validate_api_keys', return_value=True), \
         patch('src.cli.run_pipeline.ensure_directories'), \
         patch('src.cli.run_pipeline.ingest_elastic_data', return_value=sample_ingest_data), \
         patch('src.cli.run_pipeline.clean_elastic_data', return_value=sample_clean_data), \
         patch('src.cli.run_pipeline.compute_compositional_features', return_value=sample_feature_data), \
         patch('src.cli.run_pipeline.get_path', return_value=str(output_file)):
         
         # Run the main function
         # We need to patch sys.exit to prevent the script from exiting
         with patch('sys.exit') as mock_exit:
             result = main()
             
             # Verify sys.exit was called with 0 (success)
             mock_exit.assert_called_once_with(0)

             # Verify output file was created
             assert output_file.exists(), "Output CSV file was not created"
             
             # Verify content
             df = pd.read_csv(output_file)
             assert len(df) == 2
             assert 'A1' in df.columns
             assert 'radius_variance' in df.columns

def test_pipeline_empty_ingest():
    """Test pipeline behavior when ingestion returns empty data."""
    
    with patch('src.cli.run_pipeline.get_config', return_value={"paths": {}, "seed": 42}), \
         patch('src.cli.run_pipeline.validate_api_keys', return_value=True), \
         patch('src.cli.run_pipeline.ingest_elastic_data', return_value=None), \
         patch('sys.exit') as mock_exit:
            
        main()
        mock_exit.assert_called_once_with(1)

def test_pipeline_validation_flag(sample_feature_data, tmp_path):
    """Test the --validate flag functionality."""
    
    output_dir = tmp_path / "data" / "processed"
    output_dir.mkdir(parents=True)
    output_file = output_dir / "elastic_anisotropy.csv"

    # Create a dataframe with no nulls
    clean_data = sample_feature_data.copy()
    
    with patch('src.cli.run_pipeline.get_config', return_value={"paths": {}, "seed": 42}), \
         patch('src.cli.run_pipeline.validate_api_keys', return_value=True), \
         patch('src.cli.run_pipeline.ensure_directories'), \
         patch('src.cli.run_pipeline.ingest_elastic_data', return_value=clean_data), \
         patch('src.cli.run_pipeline.clean_elastic_data', return_value=clean_data), \
         patch('src.cli.run_pipeline.compute_compositional_features', return_value=clean_data), \
         patch('src.cli.run_pipeline.get_path', return_value=str(output_file)):
         
         # Simulate args with --validate
         with patch('sys.argv', ['run_pipeline.py', '--validate']):
             with patch('sys.exit') as mock_exit:
                 main()
                 mock_exit.assert_called_once_with(0)