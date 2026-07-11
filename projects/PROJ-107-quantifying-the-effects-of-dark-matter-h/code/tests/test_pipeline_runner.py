import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock the config and logging utilities to avoid dependency on full project setup during unit tests
from code.processing.pipeline_runner import validate_dataframe, MIN_AXIAL_RATIO, MAX_AXIAL_RATIO, MIN_TRIAXIALITY, MAX_TRIAXIALITY

class TestPipelineValidation:
    """Tests for T017: Aggregation and Validation logic"""

    def test_validate_dataframe_axial_ratios(self):
        """Test that invalid axial ratios are filtered out"""
        data = {
            'halo_id': [1, 2, 3, 4, 5],
            'b_a_ratio': [0.5, 0.0, 1.1, 0.8, -0.1],  # 2, 3, 5 are invalid
            'c_a_ratio': [0.4, 0.5, 0.5, 0.9, 0.5],   # 0 is valid
            'triaxiality': [0.5, 0.5, 0.5, 0.5, 0.5]
        }
        df = pd.DataFrame(data)
        
        # Mock logger
        logger = MagicMock()
        
        result = validate_dataframe(df, logger)
        
        # Only halo_id 1 and 4 should remain
        assert len(result) == 2
        assert list(result['halo_id']) == [1, 4]

    def test_validate_dataframe_triaxiality(self):
        """Test that invalid triaxiality values are filtered out"""
        data = {
            'halo_id': [1, 2, 3],
            'b_a_ratio': [0.5, 0.5, 0.5],
            'c_a_ratio': [0.5, 0.5, 0.5],
            'triaxiality': [0.5, -0.1, 1.5]  # 2 and 3 are invalid
        }
        df = pd.DataFrame(data)
        logger = MagicMock()
        
        result = validate_dataframe(df, logger)
        
        assert len(result) == 1
        assert result['halo_id'].iloc[0] == 1

    def test_validate_dataframe_all_valid(self):
        """Test that valid data passes through unchanged"""
        data = {
            'halo_id': [1, 2],
            'b_a_ratio': [0.5, 0.9],
            'c_a_ratio': [0.4, 0.8],
            'triaxiality': [0.3, 0.7]
        }
        df = pd.DataFrame(data)
        logger = MagicMock()
        
        result = validate_dataframe(df, logger)
        
        assert len(result) == 2
        pd.testing.assert_frame_equal(result, df)

    def test_validate_dataframe_empty(self):
        """Test behavior with empty dataframe"""
        df = pd.DataFrame(columns=['halo_id', 'b_a_ratio', 'c_a_ratio', 'triaxiality'])
        logger = MagicMock()
        
        result = validate_dataframe(df, logger)
        assert len(result) == 0

class TestPipelineRunnerIntegration:
    """Integration tests for the pipeline runner (requires mock data)"""

    @patch('code.processing.pipeline_runner.get_project_root')
    @patch('code.processing.pipeline_runner.get_data_processed_path')
    @patch('code.processing.pipeline_runner.load_config')
    def test_run_pipeline_creates_output(self, mock_load_config, mock_processed_path, mock_project_root):
        """Test that run_pipeline creates the expected output file with valid data"""
        # Setup mocks
        temp_dir = tempfile.mkdtemp()
        processed_dir = Path(temp_dir) / "processed"
        processed_dir.mkdir()
        
        mock_processed_path.return_value = processed_dir
        mock_project_root.return_value = Path(temp_dir)
        mock_load_config.return_value = {"chunk_size": 100}
        
        # Mock the generator to return valid records
        valid_record = {
            "halo_id": 1,
            "file": "test.hdf5",
            "associational_only": True,
            "b_a_ratio": 0.6,
            "c_a_ratio": 0.4,
            "triaxiality": 0.5,
            "particle_count": 15000
        }
        
        def mock_iterate(config, logger):
            yield valid_record
            yield {**valid_record, "halo_id": 2}
        
        with patch('code.processing.pipeline_runner.iterate_haloes', mock_iterate):
            from code.processing.pipeline_runner import run_pipeline
            success = run_pipeline()
            
            assert success is True
            output_file = processed_dir / "halo_shapes.csv"
            assert output_file.exists()
            
            df = pd.read_csv(output_file)
            assert len(df) == 2
            assert 'associational_only' in df.columns
            assert all(df['associational_only'] == True)
            assert all((df['b_a_ratio'] > 0) & (df['b_a_ratio'] <= 1))
            assert all((df['c_a_ratio'] > 0) & (df['c_a_ratio'] <= 1))

        # Cleanup
        shutil.rmtree(temp_dir)
