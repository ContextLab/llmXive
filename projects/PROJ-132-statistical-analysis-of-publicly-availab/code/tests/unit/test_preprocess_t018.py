import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import json

from src.data.preprocess import mark_insufficient_data, run_preprocessing_pipeline
from src.lib.config import setup_logging

@pytest.fixture
def sample_ebird_data():
    """Sample eBird data for testing."""
    return pd.DataFrame({
        'species': ['Species_A', 'Species_A', 'Species_A', 'Species_B', 'Species_B'],
        'lat': [40.0, 40.0, 40.0, 41.0, 41.0],
        'lon': [-75.0, -75.0, -75.0, -76.0, -76.0],
        'date': ['2023-03-01', '2023-03-08', '2023-03-15', '2023-03-01', '2023-03-08'],
        'count': [3, 1, 1, 2, 1],  # Species_A: 5 total, Species_B: 3 total
        'checklist_id': ['C1', 'C2', 'C3', 'C4', 'C5']
    })

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestMarkInsufficientData:
    """Test cases for mark_insufficient_data function (T018)."""

    def test_mark_insufficient_data_basic(self, sample_ebird_data):
        """Test basic functionality of marking insufficient data."""
        df_filtered, metadata = mark_insufficient_data(sample_ebird_data, min_observations=5)
        
        # Species_A has exactly 5 observations, should be kept
        # Species_B has 3 observations, should be filtered out
        assert len(df_filtered) == 3  # Only Species_A rows
        assert 'Species_B' not in df_filtered['species'].values
        
        # Check metadata
        assert metadata['total_cells'] >= 1
        assert metadata['insufficient_cells'] >= 1
        assert metadata['threshold'] == 5
        assert len(metadata['cells']) >= 1

    def test_mark_insufficient_data_all_sufficient(self, sample_ebird_data):
        """Test when all cells have sufficient data."""
        # Increase counts to make all sufficient
        df = sample_ebird_data.copy()
        df['count'] = [10, 10, 10, 10, 10]
        
        df_filtered, metadata = mark_insufficient_data(df, min_observations=5)
        
        assert len(df_filtered) == len(df)
        assert metadata['insufficient_cells'] == 0
        assert len(metadata['cells']) == 0

    def test_mark_insufficient_data_all_insufficient(self, sample_ebird_data):
        """Test when all cells have insufficient data."""
        df = sample_ebird_data.copy()
        df['count'] = [1, 1, 1, 1, 1]
        
        df_filtered, metadata = mark_insufficient_data(df, min_observations=5)
        
        assert len(df_filtered) == 0
        assert metadata['insufficient_cells'] > 0

    def test_mark_insufficient_data_logs_to_file(self, sample_ebird_data, temp_data_dir):
        """Test that insufficient data is logged to file."""
        log_file = temp_data_dir / 'test.log'
        
        df_filtered, metadata = mark_insufficient_data(
            sample_ebird_data, 
            min_observations=5, 
            log_file=log_file
        )
        
        assert log_file.exists()
        content = log_file.read_text()
        assert 'Insufficient data' in content
        assert 'Species_B' in content  # Species_B should be flagged

    def test_mark_insufficient_data_metadata_structure(self, sample_ebird_data):
        """Test metadata structure is correct."""
        df_filtered, metadata = mark_insufficient_data(sample_ebird_data, min_observations=5)
        
        assert 'total_cells' in metadata
        assert 'insufficient_cells' in metadata
        assert 'threshold' in metadata
        assert 'cells' in metadata
        assert isinstance(metadata['cells'], list)
        
        if len(metadata['cells']) > 0:
            cell = metadata['cells'][0]
            assert 'species' in cell
            assert 'grid_cell' in cell
            assert 'observations' in cell
            assert 'reason' in cell

    def test_mark_insufficient_data_data_quality_flag(self, sample_ebird_data):
        """Test that filtered data has data_quality flag."""
        df_filtered, metadata = mark_insufficient_data(sample_ebird_data, min_observations=5)
        
        if len(df_filtered) > 0:
            assert 'data_quality' in df_filtered.columns
            assert all(df_filtered['data_quality'] == 'sufficient')

    def test_mark_insufficient_data_edge_cases(self):
        """Test edge cases."""
        # Empty DataFrame
        empty_df = pd.DataFrame(columns=['species', 'lat', 'lon', 'date', 'count'])
        df_filtered, metadata = mark_insufficient_data(empty_df, min_observations=5)
        assert len(df_filtered) == 0
        assert metadata['insufficient_cells'] == 0

        # Single observation
        single_df = pd.DataFrame({
            'species': ['Species_A'],
            'lat': [40.0],
            'lon': [-75.0],
            'date': ['2023-03-01'],
            'count': [1]
        })
        df_filtered, metadata = mark_insufficient_data(single_df, min_observations=5)
        assert len(df_filtered) == 0
        assert metadata['insufficient_cells'] == 1

class TestPreprocessingPipelineT018:
    """Integration tests for preprocessing pipeline with T018 logic."""

    def test_run_preprocessing_pipeline_creates_metadata_file(self, temp_data_dir):
        """Test that pipeline creates metadata_insufficient_cells.json."""
        input_dir = temp_data_dir / 'input'
        output_dir = temp_data_dir / 'output'
        state_dir = temp_data_dir / 'state'
        
        input_dir.mkdir()
        output_dir.mkdir()
        state_dir.mkdir()
        
        # Create sample input data
        input_file = input_dir / 'ebird.csv'
        sample_data = pd.DataFrame({
            'species': ['Species_A', 'Species_A', 'Species_B'],
            'lat': [40.0, 40.0, 41.0],
            'lon': [-75.0, -75.0, -76.0],
            'date': ['2023-03-01', '2023-03-08', '2023-03-15'],
            'count': [3, 1, 2],
            'checklist_id': ['C1', 'C2', 'C3']
        })
        sample_data.to_csv(input_file, index=False)
        
        result = run_preprocessing_pipeline(input_dir, output_dir, state_dir)
        
        metadata_file = output_dir / 'metadata_insufficient_cells.json'
        assert metadata_file.exists()
        
        # Verify JSON structure
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        assert 'total_cells' in metadata
        assert 'insufficient_cells' in metadata
        assert 'cells' in metadata

    def test_run_preprocessing_pipeline_excludes_insufficient_cells(self, temp_data_dir):
        """Test that pipeline excludes insufficient cells from output."""
        input_dir = temp_data_dir / 'input'
        output_dir = temp_data_dir / 'output'
        state_dir = temp_data_dir / 'state'
        
        input_dir.mkdir()
        output_dir.mkdir()
        state_dir.mkdir()
        
        # Create sample input data with insufficient observations
        input_file = input_dir / 'ebird.csv'
        sample_data = pd.DataFrame({
            'species': ['Species_A', 'Species_A', 'Species_B'],
            'lat': [40.0, 40.0, 41.0],
            'lon': [-75.0, -75.0, -76.0],
            'date': ['2023-03-01', '2023-03-08', '2023-03-15'],
            'count': [3, 1, 2],  # Species_A: 4, Species_B: 2 (both < 5)
            'checklist_id': ['C1', 'C2', 'C3']
        })
        sample_data.to_csv(input_file, index=False)
        
        result = run_preprocessing_pipeline(input_dir, output_dir, state_dir)
        
        # Load output
        output_file = output_dir / 'processed_data.parquet'
        assert output_file.exists()
        
        output_df = pd.read_parquet(output_file)
        
        # Both species should be filtered out (total < 5)
        assert len(output_df) == 0 or all(output_df['data_quality'] == 'sufficient')
        
        # Check metadata
        assert result['insufficient_cells'] > 0
