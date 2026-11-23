import os
import pandas as pd
import pytest
from datetime import datetime

from save_synthetic_data import ensure_directory_exists, add_simulation_metadata, save_synthetic_datasets

class TestEnsureDirectoryExists:
    def test_creates_directory_if_not_exists(self, tmp_path):
        """Test that ensure_directory_exists creates a new directory."""
        new_dir = tmp_path / "new_subdir"
        assert not new_dir.exists()
        
        ensure_directory_exists(str(new_dir))
        
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_does_not_error_if_exists(self, tmp_path):
        """Test that ensure_directory_exists doesn't error if dir exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        # Should not raise
        ensure_directory_exists(str(existing_dir))
        
        assert existing_dir.exists()

class TestAddSimulationMetadata:
    def test_adds_required_flags(self):
        """Test that simulation metadata flags are added correctly."""
        df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'recall': [1, 0, 1],
            'bizarreness': [3, 5, 2]
        })
        
        protocol_params = {
            'seed': 42,
            'effect_size': 'moderate_positive'
        }
        
        result = add_simulation_metadata(df, protocol_params)
        
        # Check new columns exist
        assert 'is_simulation' in result.columns
        assert 'simulation_timestamp' in result.columns
        assert 'simulation_seed' in result.columns
        assert 'source' in result.columns
        assert 'effect_size_scenario' in result.columns
        
        # Check values
        assert result['is_simulation'].all()
        assert (result['source'] == 'synthetic_simulation').all()
        assert result['simulation_seed'].iloc[0] == 42
        assert result['effect_size_scenario'].iloc[0] == 'moderate_positive'
        
        # Check timestamp format
        try:
            datetime.fromisoformat(result['simulation_timestamp'].iloc[0])
        except ValueError:
            pytest.fail("simulation_timestamp is not in ISO format")

    def test_preserves_original_data(self):
        """Test that original data columns are preserved."""
        original_df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'recall': [1, 0, 1],
            'bizarreness': [3, 5, 2],
            'condition': ['strict', 'moderate', 'partial']
        })
        
        result = add_simulation_metadata(original_df, {})
        
        # Check original columns preserved
        for col in original_df.columns:
            assert col in result.columns
            assert list(result[col]) == list(original_df[col])

class TestSaveSyntheticDatasets:
    def test_creates_files_in_output_dir(self, tmp_path, monkeypatch):
        """Test that save_synthetic_datasets creates files in the output directory."""
        output_dir = tmp_path / "synthetic_output"
        
        # Mock the generate_synthetic_datasets to return known data
        mock_datasets = {
            'positive_effect': pd.DataFrame({
                'participant_id': [1, 2],
                'recall': [1, 0],
                'bizarreness': [4, 3]
            }),
            'null_effect': pd.DataFrame({
                'participant_id': [3, 4],
                'recall': [0, 1],
                'bizarreness': [5, 5]
            })
        }
        
        # Mock load_protocol
        mock_protocol = {'seed': 123, 'effect_size': 'test'}
        
        def mock_load_protocol():
            return mock_protocol
        
        def mock_generate_synthetic_datasets():
            return mock_datasets
        
        monkeypatch.setattr('save_synthetic_data.load_protocol', mock_load_protocol)
        monkeypatch.setattr('save_synthetic_data.generate_synthetic_datasets', mock_generate_synthetic_datasets)
        
        # Run the function
        save_synthetic_datasets(str(output_dir))
        
        # Check files were created
        assert (output_dir / "synthetic_positive_effect.csv").exists()
        assert (output_dir / "synthetic_null_effect.csv").exists()
        
        # Check content of one file
        saved_df = pd.read_csv(output_dir / "synthetic_positive_effect.csv")
        assert 'is_simulation' in saved_df.columns
        assert saved_df['is_simulation'].all()
        assert 'source' in saved_df.columns
        assert (saved_df['source'] == 'synthetic_simulation').all()
        assert 'simulation_seed' in saved_df.columns
        assert saved_df['simulation_seed'].iloc[0] == 123