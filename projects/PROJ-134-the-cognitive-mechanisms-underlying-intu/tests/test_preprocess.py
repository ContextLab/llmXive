"""
Unit tests for the preprocessing module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import tempfile
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.preprocess import (
    load_merged_data,
    load_blend_shape_config,
    assign_salience_level,
    map_to_blend_shapes,
    process_salience_mapping,
    save_preprocessed_data,
    run_preprocessing_pipeline
)
from code.utils.schema import SalienceLevel


class TestPreprocess:
    """Test suite for preprocessing functions."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_merged_data(self, temp_dir):
        """Create a sample merged CSV file."""
        data = {
            'story_id': ['story_001', 'story_002', 'story_003'],
            'participant_id': ['p1', 'p2', 'p3'],
            'judgment': [5, 3, 4],
            'foundation_score': [0.8, 0.5, 0.6]
        }
        df = pd.DataFrame(data)
        path = temp_dir / "merged_data.csv"
        df.to_csv(path, index=False)
        return path

    @pytest.fixture
    def sample_config(self, temp_dir):
        """Create a sample blend shape config file."""
        config = {
            'story_mappings': {
                'story_001': {
                    'salience_level': 'high',
                    'blend_shapes': {'eye_open': 0.8, 'mouth_smile': 0.6}
                },
                'story_002': {
                    'salience_level': 'low',
                    'blend_shapes': {'eye_open': 0.4, 'mouth_smile': 0.2}
                },
                'story_003': {
                    'salience_level': 'high',
                    'blend_shapes': {'eye_open': 0.9, 'mouth_smile': 0.7}
                }
            }
        }
        path = temp_dir / "unity_blend_shapes.yaml"
        with open(path, 'w') as f:
            yaml.dump(config, f)
        return path

    def test_load_merged_data(self, sample_merged_data):
        """Test loading merged data."""
        df = load_merged_data(sample_merged_data)
        assert len(df) == 3
        assert 'story_id' in df.columns
        assert list(df['story_id']) == ['story_001', 'story_002', 'story_003']

    def test_load_merged_data_not_found(self, temp_dir):
        """Test loading non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_merged_data(temp_dir / "nonexistent.csv")

    def test_load_merged_data_empty(self, temp_dir):
        """Test loading empty file."""
        path = temp_dir / "empty.csv"
        path.touch()
        with pytest.raises(ValueError):
            load_merged_data(path)

    def test_load_blend_shape_config(self, sample_config):
        """Test loading blend shape config."""
        config = load_blend_shape_config(sample_config)
        assert 'story_mappings' in config
        assert 'story_001' in config['story_mappings']
        assert config['story_mappings']['story_001']['salience_level'] == 'high'

    def test_load_blend_shape_config_not_found(self, temp_dir):
        """Test loading non-existent config."""
        with pytest.raises(FileNotFoundError):
            load_blend_shape_config(temp_dir / "nonexistent.yaml")

    def test_assign_salience_level_found(self, sample_config):
        """Test assigning salience level when found."""
        config = load_blend_shape_config(sample_config)
        level = assign_salience_level('story_001', config)
        assert level == 'high'
        
        level = assign_salience_level('story_002', config)
        assert level == 'low'

    def test_assign_salience_level_not_found(self, sample_config):
        """Test assigning salience level when not found (defaults to low)."""
        config = load_blend_shape_config(sample_config)
        level = assign_salience_level('story_999', config)
        assert level == 'low'

    def test_map_to_blend_shapes(self, sample_merged_data, sample_config):
        """Test mapping stories to blend shapes."""
        df = load_merged_data(sample_merged_data)
        config = load_blend_shape_config(sample_config)
        
        result_df = map_to_blend_shapes(df, config)
        
        assert 'salience_level' in result_df.columns
        assert len(result_df) == 3
        assert result_df.loc[result_df['story_id'] == 'story_001', 'salience_level'].iloc[0] == 'high'
        assert result_df.loc[result_df['story_id'] == 'story_002', 'salience_level'].iloc[0] == 'low'

    def test_map_to_blend_shapes_invalid_salience(self, temp_dir):
        """Test mapping with invalid salience level."""
        # Create data
        data = {'story_id': ['s1']}
        df = pd.DataFrame(data)
        path = temp_dir / "data.csv"
        df.to_csv(path, index=False)
        
        # Create config with invalid salience
        config = {
            'story_mappings': {
                's1': {'salience_level': 'invalid'}
            }
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        df_loaded = load_merged_data(path)
        cfg = load_blend_shape_config(config_path)
        
        # Should raise error because 'invalid' is not in ['low', 'high']
        with pytest.raises(ValueError):
            map_to_blend_shapes(df_loaded, cfg)

    def test_save_preprocessed_data(self, sample_merged_data, sample_config, temp_dir):
        """Test saving preprocessed data."""
        df = load_merged_data(sample_merged_data)
        config = load_blend_shape_config(sample_config)
        df = map_to_blend_shapes(df, config)
        
        output_path = temp_dir / "output.csv"
        save_preprocessed_data(df, output_path)
        
        assert output_path.exists()
        result_df = pd.read_csv(output_path)
        assert len(result_df) == 3
        assert 'salience_level' in result_df.columns

    def test_run_preprocessing_pipeline(self, sample_merged_data, sample_config, temp_dir):
        """Test the full preprocessing pipeline."""
        output_path = temp_dir / "preprocessed.csv"
        log_path = temp_dir / "vr_mapping.log"
        
        result_df = run_preprocessing_pipeline(
            sample_merged_data,
            sample_config,
            output_path,
            log_path
        )
        
        assert output_path.exists()
        assert log_path.exists()
        assert len(result_df) == 3
        assert 'salience_level' in result_df.columns
        
        # Verify log content
        with open(log_path, 'r') as f:
            log_content = f.read()
            assert 'story_001' in log_content
            assert 'high' in log_content

    def test_run_preprocessing_pipeline_missing_input(self, temp_dir):
        """Test pipeline with missing input file."""
        config_path = temp_dir / "config.yaml"
        output_path = temp_dir / "output.csv"
        
        with pytest.raises(FileNotFoundError):
            run_preprocessing_pipeline(
                temp_dir / "missing.csv",
                config_path,
                output_path
            )

    def test_run_preprocessing_pipeline_missing_config(self, sample_merged_data, temp_dir):
        """Test pipeline with missing config file."""
        output_path = temp_dir / "output.csv"
        
        with pytest.raises(FileNotFoundError):
            run_preprocessing_pipeline(
                sample_merged_data,
                temp_dir / "missing.yaml",
                output_path
            )