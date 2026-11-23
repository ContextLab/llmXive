"""
Unit tests for saving synthetic data with simulation metadata.
"""

import os
import json
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import the function to test
from save_synthetic_data import (
    add_simulation_metadata,
    save_synthetic_datasets,
    ensure_directory_exists
)

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    return pd.DataFrame({
        'condition': ['strict', 'moderate', 'partial'] * 10,
        'recall': [1, 0, 1] * 10,
        'bizarreness': [3, 5, 7] * 10,
        'participant_id': list(range(30))
    })

@pytest.fixture
def mock_protocol():
    """Mock protocol parameters."""
    return {
        'N': 200,
        'ICC': 0.3,
        'effect_sizes': {
            'positive_effect': 0.5,
            'null_effect': 0.0,
            'negative_effect': -0.2
        }
    }

class TestAddSimulationMetadata:
    def test_adds_simulation_source_column(self, sample_dataframe, mock_protocol):
        """Test that simulation_source column is added."""
        df_with_meta = add_simulation_metadata(sample_dataframe, 'test_scenario', mock_protocol)
        assert 'simulation_source' in df_with_meta.columns
        assert all(df_with_meta['simulation_source'] == 'Simulation-based')

    def test_adds_scenario_column(self, sample_dataframe, mock_protocol):
        """Test that simulation_scenario column is added."""
        df_with_meta = add_simulation_metadata(sample_dataframe, 'positive_effect', mock_protocol)
        assert 'simulation_scenario' in df_with_meta.columns
        assert all(df_with_meta['simulation_scenario'] == 'positive_effect')

    def test_adds_timestamp_column(self, sample_dataframe, mock_protocol):
        """Test that simulation_timestamp column is added."""
        df_with_meta = add_simulation_metadata(sample_dataframe, 'test', mock_protocol)
        assert 'simulation_timestamp' in df_with_meta.columns
        assert all(pd.notna(df_with_meta['simulation_timestamp']))

    def test_preserves_original_columns(self, sample_dataframe, mock_protocol):
        """Test that original columns are preserved."""
        df_with_meta = add_simulation_metadata(sample_dataframe, 'test', mock_protocol)
        original_cols = ['condition', 'recall', 'bizarreness', 'participant_id']
        for col in original_cols:
            assert col in df_with_meta.columns
            assert list(df_with_meta[col]) == list(sample_dataframe[col])

class TestEnsureDirectoryExists:
    def test_creates_directory_if_not_exists(self, tmp_path):
        """Test that directory is created if it doesn't exist."""
        new_dir = tmp_path / "new_subdir"
        ensure_directory_exists(str(new_dir))
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_no_error_if_directory_exists(self, tmp_path):
        """Test that no error occurs if directory already exists."""
        ensure_directory_exists(str(tmp_path))
        assert tmp_path.exists()

class TestSaveSyntheticDatasets:
    @patch('save_synthetic_data.load_protocol')
    @patch('save_synthetic_data.generate_synthetic_datasets')
    @patch('save_synthetic_data.add_simulation_metadata')
    def test_saves_files_with_metadata(self, mock_add_meta, mock_gen_datasets, mock_load_protocol, tmp_path):
        """Test that files are saved with metadata."""
        # Setup mocks
        mock_load_protocol.return_value = {'N': 200, 'ICC': 0.3, 'effect_sizes': {}}
        
        mock_df = pd.DataFrame({
            'condition': ['strict'] * 10,
            'recall': [1] * 10,
            'bizarreness': [5] * 10,
            'participant_id': list(range(10))
        })
        
        mock_gen_datasets.return_value = {'test_scenario': mock_df}
        mock_add_meta.return_value = mock_df.copy()
        mock_add_meta.return_value['simulation_source'] = 'Simulation-based'
        
        output_dir = tmp_path / "synthetic"
        saved_files = save_synthetic_datasets(str(output_dir))
        
        # Verify files were created
        assert len(saved_files) == 1
        assert os.path.exists(saved_files[0])
        assert 'synthetic_test_scenario.csv' in saved_files[0]
        
        # Verify metadata file was created
        metadata_file = tmp_path / "synthetic" / "synthetic_metadata.json"
        assert os.path.exists(metadata_file)
        
        # Verify metadata content
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            assert metadata['data_source'] == 'Simulation-based'
            assert 'datasets' in metadata
            assert len(metadata['datasets']) == 1

    @patch('save_synthetic_data.load_protocol')
    @patch('save_synthetic_data.generate_synthetic_datasets')
    def test_raises_error_on_missing_columns(self, mock_gen_datasets, mock_load_protocol, tmp_path):
        """Test that error is raised when required columns are missing."""
        mock_load_protocol.return_value = {'N': 200, 'ICC': 0.3, 'effect_sizes': {}}
        
        # Create dataframe without required columns
        mock_df = pd.DataFrame({
            'condition': ['strict'] * 10,
            'recall': [1] * 10
            # Missing 'bizarreness' and 'participant_id'
        })
        
        mock_gen_datasets.return_value = {'test': mock_df}
        
        output_dir = tmp_path / "synthetic"
        
        with pytest.raises(ValueError, match="Missing required columns"):
            save_synthetic_datasets(str(output_dir))