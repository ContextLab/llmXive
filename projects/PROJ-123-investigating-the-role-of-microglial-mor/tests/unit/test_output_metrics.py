"""
Unit tests for T019: Output Metrics Pipeline.
Verifies that the CSV is generated with correct columns and no excluded rows.
"""
import os
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.output_metrics import run_output_pipeline, process_image_file
from code.config import get_path

def test_output_pipeline_columns():
    """Test that the output CSV contains all required columns."""
    # Mock the ingestion and processing to return a known valid row
    mock_metadata = {
        'brain_region': 'Hippocampus',
        'pathology_status': 'Normal',
        'cognitive_score': 120.5
    }
    
    mock_row = {
        'file_path': 'fake/path.png',
        'brain_region': 'Hippocampus',
        'pathology_status': 'Normal',
        'branch_points': 10,
        'total_length': 500.0,
        'soma_area': 25.0,
        'sholl_intersections': 5,
        'cognitive_score': 120.5
    }

    with patch('code.output_metrics.ingest_directory') as mock_ingest, \
         patch('code.output_metrics.process_image_file') as mock_process, \
         patch('code.output_metrics.get_path') as mock_get_path, \
         patch('code.output_metrics.ensure_dirs'):
        
        mock_ingest.return_value = [('fake/path.png', mock_metadata)]
        mock_process.return_value = mock_row
        mock_get_path.side_effect = lambda *args, **kwargs: Path('data/processed/morphological_metrics.csv') if 'morphological_metrics' in str(args) else Path('data/raw')

        # Run the pipeline
        output_path = run_output_pipeline()

        # Verify the file was written
        assert os.path.exists(output_path), f"Output file {output_path} was not created"

        # Verify columns
        df = pd.read_csv(output_path)
        expected_cols = [
            'file_path', 'brain_region', 'pathology_status',
            'branch_points', 'total_length', 'soma_area',
            'sholl_intersections', 'cognitive_score'
        ]
        for col in expected_cols:
            assert col in df.columns, f"Missing required column: {col}"

def test_excluded_rows_not_in_output():
    """Test that rows with missing cognitive scores are excluded."""
    mock_metadata_missing = {
        'brain_region': 'Hippocampus',
        'pathology_status': 'Normal',
        'cognitive_score': None  # Missing score
    }
    
    mock_metadata_valid = {
        'brain_region': 'Prefrontal Cortex',
        'pathology_status': 'Early AD',
        'cognitive_score': 80.0
    }

    with patch('code.output_metrics.ingest_directory') as mock_ingest, \
         patch('code.output_metrics.process_image_file') as mock_process, \
         patch('code.output_metrics.get_path') as mock_get_path, \
         patch('code.output_metrics.ensure_dirs'):
        
        # Return two items, one valid, one invalid
        mock_ingest.return_value = [
            ('fake/missing.png', mock_metadata_missing),
            ('fake/valid.png', mock_metadata_valid)
        ]
        
        # process_image_file should only be called for the valid one if logic is correct
        # But we mock it to just return the row if called
        mock_process.return_value = {
            'file_path': 'fake/valid.png',
            'brain_region': 'Prefrontal Cortex',
            'pathology_status': 'Early AD',
            'branch_points': 5,
            'total_length': 200.0,
            'soma_area': 10.0,
            'sholl_intersections': 2,
            'cognitive_score': 80.0
        }

        mock_get_path.side_effect = lambda *args, **kwargs: Path('data/processed/morphological_metrics.csv') if 'morphological_metrics' in str(args) else Path('data/raw')

        output_path = run_output_pipeline()
        df = pd.read_csv(output_path)

        # Should only have 1 row (the valid one)
        assert len(df) == 1
        assert df.iloc[0]['file_path'] == 'fake/valid.png'

def test_invalid_brain_region_excluded():
    """Test that rows with invalid brain regions are excluded."""
    mock_metadata_invalid = {
        'brain_region': 'Cerebellum', # Invalid per schema
        'pathology_status': 'Normal',
        'cognitive_score': 100.0
    }

    with patch('code.output_metrics.ingest_directory') as mock_ingest, \
         patch('code.output_metrics.process_image_file') as mock_process, \
         patch('code.output_metrics.get_path') as mock_get_path, \
         patch('code.output_metrics.ensure_dirs'):
        
        mock_ingest.return_value = [('fake/bad.png', mock_metadata_invalid)]
        mock_process.return_value = None # Simulate skipping in process_image_file
        
        mock_get_path.side_effect = lambda *args, **kwargs: Path('data/processed/morphological_metrics.csv') if 'morphological_metrics' in str(args) else Path('data/raw')

        output_path = run_output_pipeline()
        df = pd.read_csv(output_path)

        # Should be empty
        assert len(df) == 0