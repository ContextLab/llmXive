"""
Integration test for TNG-100 download and chunk processing.

This test verifies the end-to-end pipeline:
1. Attempts to fetch TNG-100 snapshot metadata (specifically Snapshot 000).
2. Processes a representative subset of haloes using the chunked pipeline runner.
3. Validates that the output CSV contains valid axial ratios and triaxiality.
4. Ensures haloes with <10k particles are excluded.
"""
import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import pandas as pd
import requests

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_project_root, get_data_raw_path, get_data_processed_path
from processing.pipeline_runner import run_pipeline
from ingestion.tng_loader import fetch_tng_snapshot_list, download_halo_file
from utils.logging import get_pipeline_logger


class TestTNGPipelineIntegration:
    """Integration tests for the TNG-100 pipeline."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup temporary directories and cleanup after test."""
        self.project_root = get_project_root()
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock data paths to point to temp directory to avoid polluting real data
        self.original_raw_path = get_data_raw_path()
        self.original_processed_path = get_data_processed_path()
        
        # We will patch the config functions to return our temp paths during the test
        # But since config functions are imported, we patch the functions themselves
        
        yield
        
        # Cleanup
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('ingestion.tng_loader.requests.get')
    def test_fetch_snapshot_list(self, mock_get):
        """Test fetching the list of files for Snapshot 000."""
        # Mock response for TNG API
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Simulated API response structure for snapshot 000 halos
        mock_response.json.return_value = {
            "count": 2,
            "results": [
                {
                    "id": 1,
                    "snap_num": 0,
                    "halo_id": 100,
                    "num_part": 15000,
                    "file": "halos_000_100.hdf5"
                },
                {
                    "id": 2,
                    "snap_num": 0,
                    "halo_id": 101,
                    "num_part": 8000,  # Should be filtered out
                    "file": "halos_000_101.hdf5"
                }
            ]
        }
        mock_get.return_value = mock_response

        # Call the function
        from ingestion.tng_loader import fetch_tng_snapshot_list
        result = fetch_tng_snapshot_list(0)

        # Assertions
        assert result is not None
        assert len(result) == 2
        assert result[0]['halo_id'] == 100
        assert result[1]['halo_id'] == 101
        mock_get.assert_called_once()

    @patch('ingestion.tng_loader.requests.get')
    @patch('ingestion.tng_loader.open', new_callable=mock_open)
    @patch('ingestion.tng_loader.Path')
    def test_download_halo_file(self, mock_path, mock_open_file, mock_get):
        """Test downloading a single halo file."""
        # Mock the file path
        mock_file_path = MagicMock()
        mock_file_path.exists.return_value = False
        mock_path.return_value = mock_file_path

        # Mock response for file download
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"fake_hdf5_data"]
        mock_get.return_value = mock_response

        # Call the function
        from ingestion.tng_loader import download_halo_file
        result = download_halo_file("http://example.com/file.hdf5", "test.hdf5")

        # Assertions
        assert result == mock_file_path
        mock_get.assert_called_once()
        mock_open_file.assert_called_once_with(mock_file_path, 'wb')

    @patch('ingestion.tng_loader.fetch_tng_snapshot_list')
    @patch('processing.pipeline_runner.iter_halo_data_chunked')
    def test_pipeline_execution_and_output(self, mock_iter_halo, mock_fetch_list):
        """
        Full integration test: 
        1. Mock fetching the snapshot list.
        2. Mock iterating over halo data to simulate processing.
        3. Verify the output CSV is created with valid data.
        """
        # Setup mock for fetch_tng_snapshot_list
        mock_fetch_list.return_value = [
            {'halo_id': 100, 'num_part': 15000, 'file': 'halo_100.hdf5'},
            {'halo_id': 101, 'num_part': 8000, 'file': 'halo_101.hdf5'}, # Should be filtered
            {'halo_id': 102, 'num_part': 20000, 'file': 'halo_102.hdf5'}
        ]

        # Setup mock for iter_halo_data_chunked to yield simulated halo data
        # We simulate 3 haloes: 2 valid (>10k), 1 invalid (<10k)
        def mock_generator(halo_list, chunk_size=100):
            # Yield data for halo 100
            yield {
                'halo_id': 100,
                'num_part': 15000,
                'positions': np.random.rand(15000, 3),
                'velocities': np.random.rand(15000, 3),
                'masses': np.ones(15000)
            }
            # Yield data for halo 101 (should be filtered)
            yield {
                'halo_id': 101,
                'num_part': 8000,
                'positions': np.random.rand(8000, 3),
                'velocities': np.random.rand(8000, 3),
                'masses': np.ones(8000)
            }
            # Yield data for halo 102
            yield {
                'halo_id': 102,
                'num_part': 20000,
                'positions': np.random.rand(20000, 3),
                'velocities': np.random.rand(20000, 3),
                'masses': np.ones(20000)
            }

        mock_iter_halo.side_effect = lambda hl, cs: mock_generator(hl, cs)

        # Create a temporary output directory for this test
        test_output_dir = os.path.join(self.temp_dir, "processed")
        os.makedirs(test_output_dir, exist_ok=True)

        # Mock the config path functions to use our temp directory
        with patch('utils.config.get_data_processed_path', return_value=test_output_dir):
            with patch('utils.config.get_data_raw_path', return_value=self.temp_dir):
                # Run the pipeline
                # We need to patch the logger to avoid file handle issues in test env
                with patch('utils.logging.get_pipeline_logger') as mock_logger:
                    mock_logger.return_value = MagicMock()
                    
                    success = run_pipeline(
                        snapshot=0,
                        output_dir=test_output_dir,
                        max_haloes=5
                    )

        # Assertions
        assert success is True, "Pipeline should complete successfully"
        
        output_file = os.path.join(test_output_dir, "halo_shapes.csv")
        assert os.path.exists(output_file), f"Output file {output_file} should exist"
        
        # Read and validate output
        df = pd.read_csv(output_file)
        
        # Check that we have the expected columns
        expected_cols = ['halo_id', 'num_part', 'b_a_ratio', 'c_a_ratio', 'triaxiality', 'shape_bin']
        for col in expected_cols:
            assert col in df.columns, f"Column {col} missing from output"

        # Check filtering: Only haloes with num_part >= 10000 should be present
        assert (df['num_part'] >= 10000).all(), "All haloes in output must have >= 10000 particles"
        assert 101 not in df['halo_id'].values, "Halo 101 (8000 particles) should be excluded"
        assert 100 in df['halo_id'].values, "Halo 100 should be present"
        assert 102 in df['halo_id'].values, "Halo 102 should be present"

        # Check axial ratio constraints: 0 < b/a <= 1, 0 < c/a <= 1
        assert (df['b_a_ratio'] > 0).all() and (df['b_a_ratio'] <= 1).all(), "b/a ratio must be in (0, 1]"
        assert (df['c_a_ratio'] > 0).all() and (df['c_a_ratio'] <= 1).all(), "c/a ratio must be in (0, 1]"

        # Check triaxiality constraint: 0 <= T <= 1
        assert (df['triaxiality'] >= 0).all() and (df['triaxiality'] <= 1).all(), "Triaxiality must be in [0, 1]"

        # Check shape bin values
        valid_bins = ['prolate', 'triaxial', 'spherical', 'unknown']
        assert df['shape_bin'].isin(valid_bins).all(), "Shape bin must be a valid category"

        print(f"Integration test passed. Output file: {output_file}")
        print(f"Processed {len(df)} valid haloes out of {len(mock_fetch_list.return_value)} candidates.")

    @patch('ingestion.tng_loader.fetch_tng_snapshot_list')
    def test_pipeline_handles_api_failure(self, mock_fetch_list):
        """Test that the pipeline fails loudly if the API is unreachable."""
        mock_fetch_list.side_effect = requests.exceptions.ConnectionError("API Unreachable")
        
        test_output_dir = os.path.join(self.temp_dir, "processed_fail")
        os.makedirs(test_output_dir, exist_ok=True)

        with patch('utils.config.get_data_processed_path', return_value=test_output_dir):
            with patch('utils.config.get_data_raw_path', return_value=self.temp_dir):
                with patch('utils.logging.get_pipeline_logger') as mock_logger:
                    mock_logger.return_value = MagicMock()
                    
                    # The pipeline should raise an exception, not return False silently
                    # unless it catches and re-raises. We expect the run to fail.
                    with pytest.raises(Exception):
                        run_pipeline(snapshot=0, output_dir=test_output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])